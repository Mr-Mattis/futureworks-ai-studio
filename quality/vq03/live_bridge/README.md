# Future Works AI Studio — Live Blender View (VQ03.06)

This tool lets the owner watch **supported geometry and pose changes directly inside the running Blender GUI on El_Corredor** while ChatGPT uses a local command bridge. It is not a live video stream *inside the ChatGPT chat*. It does not expose a network endpoint or allow remote execution of arbitrary Python.

## Status / proof (2026-11-23)

- Blender 5.3 GUI instance launched and the addon `Future Works AI Studio — Live View` enabled in the user's saved preferences.
- The addon polls `Documents/futureworks-vq03/live_bridge/commands.json` every ~0.5 seconds (only while enabled).
- A sender writes validated, sequential JSON requests atomically; Blender applies allowlisted changes and responds via `ack.json`, including current frame and `gui_visible=true`.
- Actual visible Blender acknowledged real pose/frame/rig commands: seq 1–7, including a 3D IK hand target adjustment.
- Separate isolated Blender background suite **12/12 passed**, including arbitrary-code rejection, out-of-range commands, target allowlist and replay suppression.
- It never saves the Blender file, deletes assets, contacts cloud APIs, calls Runway or changes production workflows.

## Watch changes live

1. On El_Corredor, use the **newest Blender 5.3 window** (the older window opened before the addon was installed may not have it). Open:
   `%USERPROFILE%\Documents\futureworks-vq03\proof-v5\FWAI_VQ03_MECH_NISSAN_VINYL.blend`
2. Click the 3D viewport and press **N**. Choose **Future Works**.
3. Find **Future Works — Live Sync**; the status should read **Sync: ON**. If OFF, click **Start Live Sync**.
4. Keep Blender open while ChatGPT sends development instructions through `send_live_command.py`. Your viewport and timeline will update without reloading or opening different project files.
5. Optional: choose the other **Future Works — VQ03** panel for A/B/C pose buttons, manual playback, and rig selection.

Example local manual commands from PowerShell:

```powershell
$py = "$env:USERPROFILE\Documents\futureworks-p04-comfyui\.venv\Scripts\python.exe"
$sender = "$env:USERPROFILE\Documents\futureworks-vq03\send_live_command.py"
& $py $sender --pose 1
& $py $sender --pose 36
& $py $sender --frame 54
& $py $sender --pose 72
& $py $sender --select-rig
```

To move one existing known IK target without editing keys or saving the file, the sender also supports:

```powershell
& $py $sender --ik-target "L HAND" --location -1.10 -1.02 1.165
```

The coordinates are **Blender meters**, not pixels. Normal undo/reopening reverts live unsaved previews. When a command is acknowledged, the sender prints its sequence, `status: ok`, frame and `gui_visible: true`.

## Boundaries and operational safety

- **Live:** selected frame, pose switch, rig selection, and bounded changes to four IK targets.
- **Not yet live:** full mesh remodeling, new asset imports, cloth simulation baking, camera motion keyframing, shader graph editing, and rendering inside the GUI. Those require future dedicated allowlisted actions; background Blender renders are not themselves streamed into the GUI.
- **No live remote video in ChatGPT:** the viewer is the actual Blender window on the computer. We cannot claim to observe the desktop display just because the addon acknowledged a command; the acknowledgement proves Blender code ran in a visible GUI process.
- **No arbitrary execution:** commands reject unrecognized verbs, targets, frames, and coordinates outside the configured safe range.
- **Single writer:** issue one command at a time, read its acknowledgement before issuing the next command.
- **No autosave:** the addon only modifies in-memory scene state and writes a small local acknowledgement. The approved canon and original production assets remain immutable.
- **Visual approval** is still blocked until the mech V2 topology, Nissan 370Z proportions and film physical contact meet acceptance criteria.

## Developer verification

```powershell
& "C:\Program Files\Blender Foundation\Blender 5.3\blender.exe" --background "$env:USERPROFILE\Documents\futureworks-vq03\proof-v5\FWAI_VQ03_MECH_NISSAN_VINYL.blend" --python "$env:USERPROFILE\Documents\futureworks-vq03\test_live_bridge.py"
```

Results written locally: `%USERPROFILE%\Documents\futureworks-vq03\live_bridge\tests.json`. Source: `quality/vq03/live_bridge/` in this draft PR. No scene assets or private receipts in Git.
