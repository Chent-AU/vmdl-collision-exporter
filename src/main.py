import tkinter as tk
from tkinter import filedialog, ttk
import os
import json
import shutil
import asyncio
import threading

from modules.file_manager import extract_vmdlc_from_dir, extract_vmdl_from_dir, copy_files_with_index, extract_addons
from modules.vrf_handler import decomp_vmdl_cs
from modules.vmdl_handler import construct_objs_from_vmdls

selected_models = []

def log(message):
    console.insert(tk.END, message + '\n')
    console.see(tk.END)

def browse_base_game_dir(entry):
    folder = filedialog.askdirectory()
    if folder:
        entry.delete(0, tk.END)
        entry.insert(0, folder)
        settings["game_install_directory"] = folder
        with open('settings.json', 'w') as f:
            json.dump(settings, f, indent=4)
        refresh_addons()

def browse_output(entry):
    folder = filedialog.askdirectory()
    if folder:
        entry.delete(0, tk.END)
        entry.insert(0, folder)

def disable(x):
    x.config(state=tk.DISABLED)
def enable(x):
    x.config(state=tk.NORMAL)

def refresh_addons():
    for widget in addon_frame.winfo_children():
        widget.destroy()
    try:
        with open('settings.json') as f:
            settings.update(json.load(f))
            base_dir = settings['game_install_directory']
            addons = extract_addons(log, base_dir)
            for addon in addons:
                rb = ttk.Radiobutton(addon_frame, text=os.path.basename(addon), variable=selected_addon_path, value=addon)
                rb.pack(anchor='w')
            if addons:
                selected_addon_path.set(addons[0])
            # Load checkbox defaults from settings
            physics_var.set(settings.get("export_physics", False))
            render_var.set(settings.get("export_render", False))
            combined_var.set(settings.get("export_combined", True))
    except Exception as e:
        log(f"[ERROR] Failed to load addons: {e}")

def select_addon():
    addon_dir = selected_addon_path.get()
    if not addon_dir:
        return
    models = extract_vmdlc_from_dir(log, addon_dir)
    build_model_selector(models)
    result_label.config(text="Models extracted. Select which to export.")

def build_model_selector(model_paths):
    for widget in model_frame.winfo_children():
        widget.destroy()
    selected_models.clear()
    for path in model_paths:
        var = tk.BooleanVar()
        chk = tk.Checkbutton(model_frame, text=os.path.basename(path), variable=var)
        chk.pack(anchor='w')
        selected_models.append((path, var))

def export_selected():
    output_dir = output_entry.get()
    threshold = float(thresh_var.get())
    use_physics = physics_var.get()
    use_render = render_var.get()
    use_combined = combined_var.get()

    if not selected_models or not output_dir or not selected_addon_path.get():
        log("[ERROR] Missing input.")
        return
    disable(exportButton)
    temp_dir = os.path.join(output_dir, '_VMDL_EXTRACTOR_temp')
    if os.path.exists(temp_dir):
        shutil.rmtree(temp_dir)
    os.makedirs(temp_dir)

    selected_paths = [path for path, var in selected_models if var.get()]
    copy_files_with_index(log, selected_paths, temp_dir)
    decomp_vmdl_cs(log, temp_dir, temp_dir)

    vmdls = extract_vmdl_from_dir(log, temp_dir)
    run_async_in_thread(
    construct_objs_from_vmdls(on_complete, log, vmdls, temp_dir, output_dir, threshold,
                              use_physics, use_render, use_combined)
    )

def on_complete(temp_dir):
    shutil.rmtree(temp_dir)
    enable(exportButton)
    log('\n\n - - - All conversions completed - - - \n\n')
    
def run_async_in_thread(coro):
    def runner():
        asyncio.run(coro)
    threading.Thread(target=runner).start()

def on_mousewheel_context(event):
    if hover_target.get() == "addons":
        addon_canvas.yview_scroll(int(-1 * (event.delta / 120)), "units")
    elif hover_target.get() == "models":
        model_canvas.yview_scroll(int(-1 * (event.delta / 120)), "units")
    else:
        main_canvas.yview_scroll(int(-1 * (event.delta / 120)), "units")

def bind_scroll_area(canvas, tag):
    canvas.bind("<Enter>", lambda e: hover_target.set(tag))
    canvas.bind("<Leave>", lambda e: hover_target.set("main"))

# === TK Window Setup ===
root = tk.Tk()
root.title("VMDL Ramp Extractor")
root.geometry("1200x800")

hover_target = tk.StringVar(value="main") 
selected_addon_path = tk.StringVar()
settings = {}

# Load settings if available
if os.path.exists("settings.json"):
    try:
        with open("settings.json") as f:
            settings = json.load(f)
    except Exception as e:
        print(f"[ERROR] Failed to load settings.json: {e}")

# === Main Horizontal Layout ===
content_frame = ttk.Frame(root)
content_frame.pack(fill="both", expand=True)

# === Left UI Panel (Canvas with Scrollbar) ===
main_canvas = tk.Canvas(content_frame)
main_scrollbar = ttk.Scrollbar(content_frame, orient="vertical", command=main_canvas.yview)
main_canvas.configure(yscrollcommand=main_scrollbar.set)

main_scrollbar.pack(side="right", fill="y")
main_canvas.pack(side="left", fill="both", expand=True)

main_frame = ttk.Frame(main_canvas)
main_canvas.create_window((0, 0), window=main_frame, anchor="nw", tags="main_frame_window")
main_canvas.bind("<Configure>", lambda e: main_canvas.itemconfig("main_frame_window", width=e.width))
main_frame.bind("<Configure>", lambda e: main_canvas.configure(scrollregion=main_canvas.bbox("all")))

# === GUI Elements ===
ttk.Label(main_frame, text="Base Game Directory:").pack(anchor='w')
base_dir_entry = ttk.Entry(main_frame, width=80)
base_dir_entry.pack()
if "game_install_directory" in settings:
    base_dir_entry.insert(0, settings["game_install_directory"])
ttk.Button(main_frame, text="Browse", command=lambda: browse_base_game_dir(base_dir_entry)).pack()

ttk.Label(main_frame, text="Output Directory:").pack(anchor='w', pady=(10, 0))
output_entry = ttk.Entry(main_frame, width=80)
output_entry.pack()
ttk.Button(main_frame, text="Browse", command=lambda: browse_output(output_entry)).pack()

ttk.Button(main_frame, text="Refresh Addons", command=refresh_addons).pack(pady=5)

# === Addons Section ===
addon_group = ttk.LabelFrame(main_frame, text="Available Addons", padding=(10, 5))
addon_group.pack(fill=tk.X, pady=(10, 0))

addon_container = ttk.Frame(addon_group, height=150)
addon_container.pack(fill=tk.X, pady=5)
addon_canvas = tk.Canvas(addon_container, height=150)
addon_scroll = ttk.Scrollbar(addon_container, orient="vertical", command=addon_canvas.yview)
addon_canvas.configure(yscrollcommand=addon_scroll.set)

addon_scroll.pack(side="right", fill="y")
addon_canvas.pack(side="left", fill="both", expand=True)
addon_frame = ttk.Frame(addon_canvas)
addon_canvas.create_window((0, 0), window=addon_frame, anchor='nw')
addon_frame.bind("<Configure>", lambda e: addon_canvas.configure(scrollregion=addon_canvas.bbox("all")))

ttk.Button(main_frame, text="Select Addon", command=select_addon).pack(pady=5)

# === Model Selector ===
model_group = ttk.LabelFrame(main_frame, text="Select Models to Export", padding=(10, 5))
model_group.pack(fill=tk.X, pady=(10, 0))

model_container = ttk.Frame(model_group, height=200)
model_container.pack(fill=tk.X, pady=5)
model_canvas = tk.Canvas(model_container, height=200)
model_scroll = ttk.Scrollbar(model_container, orient="vertical", command=model_canvas.yview)
model_canvas.configure(yscrollcommand=model_scroll.set)

model_scroll.pack(side="right", fill="y")
model_canvas.pack(side="left", fill="both", expand=True)
model_frame = ttk.Frame(model_canvas)
model_canvas.create_window((0, 0), window=model_frame, anchor='nw')
model_frame.bind("<Configure>", lambda e: model_canvas.configure(scrollregion=model_canvas.bbox("all")))

# === Export Settings Section ===
options_group = ttk.LabelFrame(main_frame, text="Export Options", padding=(10, 10))
options_group.pack(fill=tk.X, pady=(15, 0))

checkbox_frame = ttk.Frame(options_group)
checkbox_frame.pack(anchor='w', pady=(0, 10))

physics_var = tk.BooleanVar(value=settings.get("export_physics", False))
render_var = tk.BooleanVar(value=settings.get("export_render", False))
combined_var = tk.BooleanVar(value=settings.get("export_combined", True))

ttk.Checkbutton(checkbox_frame, text="Export Physics", variable=physics_var).pack(side="left", padx=5)
ttk.Checkbutton(checkbox_frame, text="Export Render", variable=render_var).pack(side="left", padx=5)
ttk.Checkbutton(checkbox_frame, text="Export Combined", variable=combined_var).pack(side="left", padx=5)

ttk.Label(options_group, text="Vertex Coplane Threshold (0.0 - 1.0):").pack(anchor='w')
thresh_var = tk.DoubleVar(value=0.99)
thresh_frame = ttk.Frame(options_group)
thresh_frame.pack(fill='x')
ttk.Scale(thresh_frame, from_=0.0, to=1.0, orient=tk.HORIZONTAL, variable=thresh_var).pack(side='left', fill='x', expand=True)
ttk.Entry(thresh_frame, textvariable=thresh_var, width=5).pack(side='right')

# === EXPORT BUTTON ===
exportButton = ttk.Button(main_frame, text="Convert Models", command=export_selected)
exportButton.pack(pady=10)
result_label = ttk.Label(main_frame, text="")
result_label.pack()

# === Console Output ===
console_frame = ttk.Frame(content_frame, width=350)
console_frame.pack(side="right", fill="y")
ttk.Label(console_frame, text="Console Output:").pack(anchor='nw', padx=5, pady=(10, 0))
console = tk.Text(console_frame, width=50)
console.pack(fill="both", expand=True, padx=5, pady=5)

# === Scroll Context ===
main_canvas.bind_all("<MouseWheel>", on_mousewheel_context)
bind_scroll_area(addon_canvas, "addons")
bind_scroll_area(model_canvas, "models")

refresh_addons()
root.mainloop()
