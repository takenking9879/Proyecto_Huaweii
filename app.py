import dash
import dash_bootstrap_components as dbc

external_stylesheets = [
    dbc.themes.CYBORG,
    "/assets/theme.css"
]

app = dash.Dash(
    __name__,
    external_stylesheets = external_stylesheets,
    use_pages = True
)

app.title = 'Dashboard_huawei_test'
app.layout = dash.page_container

def _pretrain():
    import time
    time.sleep(2)          # let Dash finish registering pages first
    try:
        from pages.get_data.get_data_8  import get_ml_models
        from pages.get_data.get_data_9  import get_ml_models as get9
        from pages.get_data.get_data_10 import get_ml
        from pages.get_data.get_data_11 import get_data_11
        print("[pretrain] Entrenando modelos en background…")
        get_ml_models()
        print("[pretrain] Slide 8 listo")
        get9()
        print("[pretrain] Slide 9 listo")
        get_ml()
        print("[pretrain] Slide 10 listo")
        get_data_11()
        print("[pretrain] Slide 11 listo")
    except Exception as e:
        print(f"[pretrain] Error: {e}")


if __name__ == "__main__":
    import threading
    threading.Thread(target=_pretrain, daemon=True).start()
    app.run(debug=True, dev_tools_ui=False, use_reloader=False)