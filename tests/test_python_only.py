from pathlib import Path
import unittest


ROOT = Path(__file__).resolve().parents[1]


class PythonOnlyArchitectureTests(unittest.TestCase):
    def test_rust_core_project_is_removed(self):
        self.assertFalse((ROOT / "rust-core").exists())

    def test_runtime_zoom_helper_has_no_native_extension_import(self):
        source = (ROOT / "src" / "parin_pdf_helpers.py").read_text(encoding="utf-8")
        self.assertNotIn("_parin_rust_core", source)
        self.assertNotIn("maturin", source)

    def test_debian_build_does_not_require_rust_tooling(self):
        script = (ROOT / "scripts" / "build-deb.sh").read_text(encoding="utf-8")
        self.assertNotIn("maturin", script)
        self.assertNotIn("rust-core", script)
        self.assertNotIn("Cargo.toml", script)

    def test_ci_uses_python_only_build_steps(self):
        workflow = (ROOT / ".github" / "workflows" / "ci.yml").read_text(encoding="utf-8")
        self.assertNotIn("Set up Rust", workflow)
        self.assertNotIn("cargo", workflow.lower())
        self.assertNotIn("maturin", workflow.lower())
        self.assertNotIn("rust-core", workflow)


if __name__ == "__main__":
    unittest.main()
