#pragma once

#include <stddef.h>
#include <stdint.h>

#ifdef __cplusplus
extern "C" {
#endif

typedef struct ParinCache ParinCache;

ParinCache *parin_cache_create(size_t max_bytes);
void parin_cache_destroy(ParinCache *cache);
int32_t parin_cache_insert(ParinCache *cache, const char *key, const uint8_t *data, size_t data_len);
ptrdiff_t parin_cache_entry_size(ParinCache *cache, const char *key);
int32_t parin_cache_copy(ParinCache *cache, const char *key, uint8_t *output, size_t output_capacity);
void parin_cache_clear(ParinCache *cache);
size_t parin_cache_used_bytes(const ParinCache *cache);

#ifdef __cplusplus
}
#endif
