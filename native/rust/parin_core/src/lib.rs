use std::collections::{HashMap, VecDeque};
use std::ffi::{c_char, CStr};
use std::panic::{catch_unwind, AssertUnwindSafe};
use std::ptr;
use std::slice;

pub struct ParinCache {
    max_bytes: usize,
    used_bytes: usize,
    entries: HashMap<String, Vec<u8>>,
    least_to_most_recent: VecDeque<String>,
}

impl ParinCache {
    fn new(max_bytes: usize) -> Self {
        Self {
            max_bytes: max_bytes.max(1),
            used_bytes: 0,
            entries: HashMap::new(),
            least_to_most_recent: VecDeque::new(),
        }
    }

    fn touch(&mut self, key: &str) {
        if let Some(index) = self.least_to_most_recent.iter().position(|item| item == key) {
            self.least_to_most_recent.remove(index);
        }
        self.least_to_most_recent.push_back(key.to_owned());
    }

    fn insert(&mut self, key: String, value: Vec<u8>) -> bool {
        if value.len() > self.max_bytes {
            return false;
        }

        if let Some(previous) = self.entries.remove(&key) {
            self.used_bytes = self.used_bytes.saturating_sub(previous.len());
            if let Some(index) = self.least_to_most_recent.iter().position(|item| item == &key) {
                self.least_to_most_recent.remove(index);
            }
        }

        while self.used_bytes.saturating_add(value.len()) > self.max_bytes {
            let Some(oldest) = self.least_to_most_recent.pop_front() else {
                break;
            };
            if let Some(evicted) = self.entries.remove(&oldest) {
                self.used_bytes = self.used_bytes.saturating_sub(evicted.len());
            }
        }

        self.used_bytes = self.used_bytes.saturating_add(value.len());
        self.entries.insert(key.clone(), value);
        self.least_to_most_recent.push_back(key);
        true
    }

    fn get(&mut self, key: &str) -> Option<&[u8]> {
        if !self.entries.contains_key(key) {
            return None;
        }
        self.touch(key);
        self.entries.get(key).map(Vec::as_slice)
    }
}

unsafe fn key_from_c(key: *const c_char) -> Option<String> {
    if key.is_null() {
        return None;
    }
    CStr::from_ptr(key).to_str().ok().map(str::to_owned)
}

#[no_mangle]
pub extern "C" fn parin_cache_create(max_bytes: usize) -> *mut ParinCache {
    catch_unwind(|| Box::into_raw(Box::new(ParinCache::new(max_bytes))))
        .unwrap_or(ptr::null_mut())
}

#[no_mangle]
pub unsafe extern "C" fn parin_cache_destroy(cache: *mut ParinCache) {
    if cache.is_null() {
        return;
    }
    let _ = catch_unwind(AssertUnwindSafe(|| drop(Box::from_raw(cache))));
}

#[no_mangle]
pub unsafe extern "C" fn parin_cache_insert(
    cache: *mut ParinCache,
    key: *const c_char,
    data: *const u8,
    data_len: usize,
) -> i32 {
    if cache.is_null() || (data.is_null() && data_len > 0) {
        return 0;
    }
    catch_unwind(AssertUnwindSafe(|| {
        let Some(key) = key_from_c(key) else { return 0 };
        let bytes = if data_len == 0 {
            Vec::new()
        } else {
            slice::from_raw_parts(data, data_len).to_vec()
        };
        if (*cache).insert(key, bytes) { 1 } else { 0 }
    }))
    .unwrap_or(0)
}

#[no_mangle]
pub unsafe extern "C" fn parin_cache_entry_size(
    cache: *mut ParinCache,
    key: *const c_char,
) -> isize {
    if cache.is_null() {
        return -1;
    }
    catch_unwind(AssertUnwindSafe(|| {
        let Some(key) = key_from_c(key) else { return -1 };
        let cache = &mut *cache;
        match cache.entries.get(&key) {
            Some(value) => isize::try_from(value.len()).unwrap_or(-1),
            None => -1,
        }
    }))
    .unwrap_or(-1)
}

#[no_mangle]
pub unsafe extern "C" fn parin_cache_copy(
    cache: *mut ParinCache,
    key: *const c_char,
    output: *mut u8,
    output_capacity: usize,
) -> i32 {
    if cache.is_null() || output.is_null() {
        return 0;
    }
    catch_unwind(AssertUnwindSafe(|| {
        let Some(key) = key_from_c(key) else { return 0 };
        let cache = &mut *cache;
        let Some(value) = cache.get(&key) else { return 0 };
        if value.len() > output_capacity {
            return 0;
        }
        ptr::copy_nonoverlapping(value.as_ptr(), output, value.len());
        1
    }))
    .unwrap_or(0)
}

#[no_mangle]
pub unsafe extern "C" fn parin_cache_clear(cache: *mut ParinCache) {
    if cache.is_null() {
        return;
    }
    let _ = catch_unwind(AssertUnwindSafe(|| {
        let cache = &mut *cache;
        cache.entries.clear();
        cache.least_to_most_recent.clear();
        cache.used_bytes = 0;
    }));
}

#[no_mangle]
pub unsafe extern "C" fn parin_cache_used_bytes(cache: *const ParinCache) -> usize {
    if cache.is_null() {
        return 0;
    }
    catch_unwind(AssertUnwindSafe(|| (*cache).used_bytes)).unwrap_or(0)
}

#[cfg(test)]
mod tests {
    use super::ParinCache;

    #[test]
    fn evicts_least_recently_used_entries_until_within_budget() {
        let mut cache = ParinCache::new(6);
        assert!(cache.insert("page-1".into(), vec![1, 2, 3]));
        assert!(cache.insert("page-2".into(), vec![4, 5, 6]));
        assert_eq!(cache.get("page-1"), Some([1, 2, 3].as_slice()));
        assert!(cache.insert("page-3".into(), vec![7, 8, 9]));
        assert!(cache.entries.contains_key("page-1"));
        assert!(!cache.entries.contains_key("page-2"));
        assert!(cache.entries.contains_key("page-3"));
        assert!(cache.used_bytes <= 6);
    }

    #[test]
    fn rejects_entry_larger_than_total_cache_budget() {
        let mut cache = ParinCache::new(4);
        assert!(!cache.insert("large".into(), vec![0; 5]));
        assert_eq!(cache.used_bytes, 0);
        assert!(cache.entries.is_empty());
    }

    #[test]
    fn replacing_an_entry_updates_accounting() {
        let mut cache = ParinCache::new(8);
        assert!(cache.insert("page".into(), vec![0; 4]));
        assert!(cache.insert("page".into(), vec![0; 3]));
        assert_eq!(cache.used_bytes, 3);
    }
}
