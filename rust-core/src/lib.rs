use pyo3::exceptions::PyValueError;
use pyo3::prelude::*;

/// Clamp a zoom value to the same defensive bounds as the Python helper.
#[pyfunction]
fn clamp_zoom(value: f64, minimum: f64, maximum: f64) -> PyResult<f64> {
    if !minimum.is_finite() || !maximum.is_finite() || minimum <= 0.0 || maximum < minimum {
        return Err(PyValueError::new_err("invalid zoom bounds"));
    }
    if !value.is_finite() {
        return Ok(1.0_f64.max(minimum).min(maximum));
    }
    Ok(value.max(minimum).min(maximum))
}

#[pymodule]
fn _parin_rust_core(module: &Bound<'_, PyModule>) -> PyResult<()> {
    module.add_function(wrap_pyfunction!(clamp_zoom, module)?)?;
    module.add("__version__", env!("CARGO_PKG_VERSION"))?;
    Ok(())
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn clamps_zoom_values() {
        assert_eq!(clamp_zoom(99.0, 0.1, 8.0).unwrap(), 8.0);
        assert_eq!(clamp_zoom(0.01, 0.1, 8.0).unwrap(), 0.1);
        assert_eq!(clamp_zoom(f64::NAN, 0.1, 8.0).unwrap(), 1.0);
    }

    #[test]
    fn non_finite_values_use_a_default_inside_custom_bounds() {
        assert_eq!(clamp_zoom(f64::NAN, 2.0, 4.0).unwrap(), 2.0);
        assert_eq!(clamp_zoom(f64::INFINITY, 0.1, 0.4).unwrap(), 0.4);
    }

    #[test]
    fn rejects_invalid_bounds() {
        assert!(clamp_zoom(1.0, 0.0, 8.0).is_err());
        assert!(clamp_zoom(1.0, 2.0, 1.0).is_err());
        assert!(clamp_zoom(f64::NAN, 0.0, 8.0).is_err());
    }
}
