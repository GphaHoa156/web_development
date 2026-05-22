import importlib.util
from pathlib import Path


APP_FILE = Path(__file__).resolve().parent / "app" / "gradio_app.py"
spec = importlib.util.spec_from_file_location("bank_churn_gradio_app", APP_FILE)
module = importlib.util.module_from_spec(spec)
assert spec.loader is not None
spec.loader.exec_module(module)
demo = module.demo


if __name__ == "__main__":
    demo.launch(
        server_name="127.0.0.1",
        server_port=7860,
        prevent_thread_lock=False,
        css=module.APP_CSS,
        theme=module.gr.themes.Soft(),
    )
