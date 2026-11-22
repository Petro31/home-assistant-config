# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

This file is public. Hostnames, owner names and other private details live in the git-ignored `CLAUDE.local.md`. Refer to that file instead of writing those details here.

## Ground rules (read first)

This repository is the **live configuration of a running Home Assistant instance**. A bad edit can break the home's automations, dashboards, or startup. Be cautious.

- **Never modify, create, delete, move, or rename any file without explicit approval from the user.** Propose the exact change first (show the diff or new content) and wait for a clear yes. Approval for one change does not cover follow-up or related changes; ask again.
- Also get approval before any action that changes system state. That includes git commits, pushes, branch operations, reloads, restarts, and service calls.
- Read-only investigation (reading files, searching, `git log`/`git diff`/`git status`) is fine without asking.
- When proposing a change, point out anything that could break: YAML structure or indentation, include-directive shape (list vs mapping), renamed or removed entity IDs referenced elsewhere, and whether a reload or a full restart will be needed.

## What this is

The live Home Assistant `/config` directory (mounted over SMB; the share path is in `CLAUDE.local.md`), version-controlled and published publicly on GitHub (repo URL in `CLAUDE.local.md`). The current HA version is in `.HA_VERSION`. Edits made here affect the running instance once HA reloads them.

- There is no build, lint, or test tooling in the repo. Check configuration from HA itself (Developer Tools → YAML → Check configuration, or `ha core check` on the host). Then reload the affected domain (automations, scripts, templates, etc.) or restart HA.
- The repo is public: never commit `secrets.yaml` or `esphome/secrets.yaml`. Use `!secret` references instead. `.gitignore` also excludes runtime state (`.storage/`, logs, `home-assistant_v2.db`, `.cloud/`, `.zwjs/`), so treat it as the source of truth for what is tracked.
- The git default branch is `master`; the remote is named `home-assistant-config`, not `origin`.

## Configuration layout

`configuration.yaml` is just a hub. Most config is pulled in through include directives, and the merge style matters when you add files:

| Location | Included as | File format |
|---|---|---|
| `packages/` | `homeassistant: packages: !include_dir_named` | One feature per file, spanning many domains (`template:`, `automation:`, `script:`, …). The filename is the package name. Subfolders can group related packages, but the folder isn't part of the name. |
| `automations.yaml` | `automation: !include` | Managed by the UI editor; don't hand-edit |
| `scripts.yaml` | `script: !include` | Managed by the UI editor |
| `scenes.yaml` | `scene: !include` | Managed by the UI scene editor (currently empty, `[]`). The YAML scenes (no `id:`, so they aren't in the entity registry) live in packages: the holiday bulb scenes in `packages/holiday/`, the everyday outdoor bulb scenes in `packages/outdoor_sunset_lighting.yaml`. |
| `themes/` | `!include_dir_merge_named` | (git-ignored) |

The only other top-level `*.yaml` files are `secrets.yaml` and the dashboards (`ui-*.yaml`, loaded by `lovelace.yaml`). Integration settings live in packages too: `packages/system/` holds `system_recorder.yaml` (the recorder, including its include/exclude filters), `system_logging.yaml` (logger and system_log) and `system_cloud.yaml` (the Nabu Casa cloud/Alexa config), and `packages/doors.yaml` holds door_buddy. When removing an include from `configuration.yaml`, delete the file too rather than leaving it behind.

New features go in `packages/` (see `packages/leak_detection.yaml` for the current style). The old domain folders (`automation/`, `scripts/`, `template/`, `command_line/`) and flat domain files (`sensor.yaml`, `media_player.yaml`, `notify.yaml`, `compensation.yaml`) are gone; put new config of those domains in a package.

### Conventions

- Every automation gets an `id:` and every template entity gets a `unique_id:`, both random UUIDs. Generate fresh ones and never reuse them.
- Newer files use current syntax (`triggers:` / `- trigger: state`, `actions:`, `action: light.turn_on`). Older files still use `trigger:` / `platform:` / `service:`. Use the new syntax for new or rewritten code. Don't mass-migrate unrelated files unless asked; migrations are done as their own commits (e.g. `color_temp` → `color_temp_kelvin`).
- YAML anchors are common for reusing entity lists between a trigger and `variables` (`entity_id: &entities` … `entities: *entities`).
- Reusable Jinja macros live in `custom_templates/*.jinja` and are imported in templates with `{% from 'easy_time.jinja' import month_day %}`.
- `python_scripts/` holds HA `python_script` integration scripts (sandboxed, no imports), with their service schemas in `python_scripts/services.yaml`.

## Dashboards (lovelace_gen)

`lovelace.yaml` defines two YAML-mode dashboards, `ui-home.yaml` and `ui-status.yaml`. Both are built from `lovelace/`:

- `lovelace/views/`: one file per view. `master.yaml` assembles the view list for the Home dashboard.
- `lovelace/templates/` and `lovelace/partials/`: reusable card fragments.
- Files whose first line is `# lovelace_gen` are rendered as Jinja by the `lovelace_gen` custom component ([docs and source](https://github.com/thomasloven/hass-lovelace_gen)) before YAML parsing. Fragments are included with variables via the list form of `!include` (filename first, then a dict of variables):
  ```yaml
  - !include
    - '../templates/headers/navigator.yaml'
    - name: Drinks
  ```
  Inside the template, variables are plain Jinja (`{{ entity }}`, `{{ label|default(...) }}`).
- lovelace_gen specifics that commonly cause mistakes:
  - Templates render once, when the dashboard is rendered, using the variables passed in. They are **not** live: use `{% raw %}…{% endraw %}` for anything that must be evaluated by the frontend or HA (button-card JS, `{{ states(...) }}`).
  - Dicts can't be passed directly as include variables. Send them with `| tojson` and decode them with `| fromjson` (a filter lovelace_gen adds).
  - Values under `lovelace_gen:` in `configuration.yaml` are available as `_global` (currently empty here).
  - `!file /local/x.js` appends a random version to bust browser caches.
  - Macro output isn't re-indented, so macros take an explicit indent argument (see `lovelace/views/dynamic_view_builder.yaml` and the macros in `master.yaml`).
  - Don't put the `# lovelace_gen` header in the top-level dashboard files (`ui-home.yaml`, `ui-status.yaml`), only in files they include.
- Most cards are `custom:button-card` and other HACS frontend cards. `www/community/` is git-ignored.
- To pick up template edits, use **Refresh** from the dashboard's three-dot menu. Changes to `lovelace.yaml` or the `lovelace_gen:` config need an HA restart.

### How the views are built

- `ui-home.yaml` is only `views: !include lovelace/views/master.yaml`. `ui-status.yaml` points the same way at `status_master.yaml`, which follows the same pattern (with its own copy of the macros and `dashboard = 'ui-status'`).
- `master.yaml` holds the dashboard data as Jinja literals at the top: `areas` (each with `entities`, `header`, `type` and `display` rules), `doors`, `echos`, and `main_buttons` (the top-level menu; a button's `entities` can be a list of sub-buttons such as `areas` or `doors`). Most frontend changes, like adding an entity to an area or adding an area or menu button, are edits to these lists.
- Below the data, `master.yaml` writes the view list in four passes:
  1. the Home view
  2. one view per main button: its own `view:` file if it has one, otherwise `dynamic_view_builder.yaml`
  3. the person map views
  4. one generated subview per sub-button (each area and door), with `back_path` set to the parent's slug; then `remote_settings.yaml`
- Jinja dicts and lists can't be passed straight into an `!include`, so the `toyaml` / `buildmapping` / `builditerable` macros turn them back into indented YAML text inside each `!include` variable block. Their first argument is the indent string, so keep it in step with where the output lands.
- `dynamic_view_builder.yaml` is the generic view generator:
  - Each `header` entry becomes a horizontal stack between `edge.yaml` spacers. A header entry can be one card (mapping) or a row of cards (list). Header cards also get the view's `entities`, `back_path`, `name` and `icon`.
  - `entities` are split into grids of `rows` × `columns` (default 3×3); short rows are padded with `spacer`.
  - Each cell's card is chosen in this order: an explicit `type:`, then the domain lookup in `mapped_button_cards` (e.g. light/switch/fan → `toggle2.yaml`, sensor/binary_sensor → `sensor.yaml`), then `empty.yaml`.
  - A dict entry without `entity` is a navigation button to a subview.
- A view's `path` is its `name` lowercased with spaces replaced by `_`. Renaming an area or button changes its URL and the `back_path` of its subviews.
- Leaf templates are in `lovelace/templates/` (`buttons/`, `summary/`, `headers/`, `remote/`), and most are `custom:button-card` configs. `summary/overview.yaml` builds the "N lights on" style summaries at render time from `display` (domain/state/icon/units rules) and `triggers_update` (defaults to the button's `entities`). `override_sensors` sets the sensors shown in place of the leftover ones.

### Home v2 (in progress)

`ui-home-v2.yaml` (admin-only) is a rebuild of the Home dashboard in `lovelace_v2/`, using built-in cards, Mushroom, UIX and the Room Summary Card. `lovelace_v2/data/home.jinja` holds the data and `lovelace_v2/views/main.yaml` builds the views. Home has summary cards (`lovelace_v2/cards/room.yaml`) atop the Household window: the house (opens Areas; its lock and laundry icons open the Doors and Laundry subviews), the remote (opens the Remote subview, a copy of the legacy view whose cog opens Remote Settings; its music icon opens the Music subview), the holiday (opens the Holiday subview) and events (opens the Events subview; its icons open the Drinks, Irrigation and This Week subviews). Buttons with `legacy:` in `home.jinja` still open the old dashboard's view.

To do:
- [x] Holiday summary card on Home. Its icons control the current holiday's themed lights directly. The card opens a page with all lights and scenes available for the current holiday (`sensor.holiday_lighting`; legacy `lovelace/views/holiday.yaml`).
- [ ] ~~Music summary card on Home. Its icons count what's playing music in the house; the card opens a media/music page (legacy `lovelace/views/music.yaml`). One icon opens the Echo devices, which get their own control page (legacy `lovelace/views/echos.yaml`).~~ Cancelled: music is the music icon on the remote card instead (below).
- [x] Laundry: the laundry icon on the house card opens a Laundry subview, an exact copy of the current Laundry view (`lovelace/views/laundry.yaml`) apart from the back button.
- [x] Events summary card on Home. The card opens a subview copy of the Events view (`lovelace/views/events.yaml`). Its icons open subviews for Drinks (`drinks.yaml`), Irrigation (`irrigation.yaml`) and This Week (`this_week.yaml`).
- [x] Remote: recreate the Remote view (`lovelace/views/remote.yaml`) as a v2 subview, with a Remote Settings subview (`lovelace/views/remote_settings.yaml`). Then point the remote card there instead of the legacy view.
- [x] Music icon on the remote card. It opens a v2 Music page with the music controls and media players, like the legacy Music view (`lovelace/views/music.yaml`).
- [ ] Plants: figure out what to do with it. Since the Home button grid was removed, no summary card links to the Plants button (still `legacy: 'plants'`), so v2 has no way to reach it.
- [ ] Redesign the person cards on Home (`lovelace_v2/cards/person.yaml`) using the Room Summary Card, like the summary cards.
- [ ] Fully remove custom button-card from v2. It still comes in through the copied legacy views and their `lovelace/templates/` includes (e.g. Events' category buttons, Echos, the Drinks header).
- [x] Fix the broken card on the Echos subview (`lovelace_v2/views/echos.yaml`). The last-announcement button-card crashed on messages from automations (no person); it's now a Mushroom template card.

## Custom integrations

`custom_components/` is **git-ignored**: changes there are not versioned in this repo. Several of these are the owner's own projects with separate upstream repos. Make real fixes there, not here.

- Owner-maintained: `door_buddy`, `harmony_helper`, `multizone_controller` (upstream repos listed in `CLAUDE.local.md`). Their YAML config is in `packages/doors.yaml`, `packages/living_room/living_room_harmony.yaml`, and (multizone_controller) `packages/living_room/living_room_yamaha.yaml` / `packages/basement_yamaha.yaml`. Dashboard and remote templates (`custom_templates/harmony.jinja`, `lovelace/templates/remote*`) depend on harmony_helper entities.
- Third-party (HACS): `lovelace_gen`, `custom_icons`, `ge_home`, `pirateweather`, `spook`, `toyota_na`. Spook raises repairs for references to missing entities and services, so renaming or removing an entity usually means updating every reference to it.

## ESPHome

`esphome/*.yaml` are ESPHome device configs compiled by the ESPHome add-on, not loaded by HA. Their build directories (`esphome/<device>/`) and `esphome/secrets.yaml` are git-ignored.

## Package migration (ongoing)

Goal: over time, move features whose automations, scripts and templates are split across `automation/`, `scripts/` and `template/` into one file per feature in `packages/`. Do one feature per change and commit, and only when the user asks for that item.

### How to migrate a feature

- Wrap the moved content under its domain key: automations (list) under `automation:`, scripts (mapping) under `script:`, template blocks (list) under `template:`.
- **Move content unchanged.** Keep every `id` and `unique_id` exactly as they are so entity IDs, history and UI customizations survive.
- **The only changes allowed are the ones listed here.** No optimizations, refactors, reordering, reformatting, renamed entities, template rewrites or "while I'm here" fixes. If something looks wrong, mention it to the user and leave it as it is.
- **Update legacy syntax to the modern keys as part of the move.** This applies to automations, scripts and trigger-based template blocks:
  - top-level `trigger:` → `triggers:`, `condition:` → `conditions:`, `action:` → `actions:` (automations and trigger-based template blocks)
  - inside each trigger, including `wait_for_trigger:`, `platform: <type>` → `trigger: <type>`
  - inside action and sequence steps, `service: <domain.service>` → `action: <domain.service>`
  Change only the key names. Values, ordering, comments and indentation stay the same.
- **Give every template entity a `default_entity_id:`** set to its current `entity_id` from `.storage/core.entity_registry` (look it up by `unique_id`; don't derive it from the name). Put it on the line right after `name:` (see `packages/garbage_notifications.yaml`), or right after `unique_id:` when the entity has no `name:`. This keeps the entity ID tied to the YAML rather than to the name. Template entities that already have one keep it unchanged.
- **Keep all content and YAML anchors/aliases.** Never drop, inline or merge an anchor. Before merging, list the anchor names in every source file. HA doesn't reject a duplicate anchor name; the later definition silently takes over, so aliases end up pointing at the wrong content. When two source files use the same anchor name, rename one of them and every alias that refers to it. That rename is the only change allowed for anchors.
- Remove the content from its old file in the same change, or HA sees duplicate IDs and script keys. If an old file ends up empty, delete it rather than leaving it empty under an `!include_dir_merge_*` directory.
- YAML anchors only work within one file. Make sure every anchor still has its alias in the same file after the move.
- Jinja macros stay in `custom_templates/`. Integration configs with their own top-level key go in a package too (e.g. `packages/doors.yaml`, `packages/system/`).
- `!include_dir_named packages` also reads subfolders, so every `.yaml` under `packages/` is loaded as a package. A folder of non-package YAML (e.g. template lists included by a package) must start with a dot, or HA rejects each file as an invalid package. HA skips dot-folders. A plain subfolder can group related packages (e.g. `packages/living_room/`), but HA names each package after its filename alone, so names must stay unique across the whole tree: two files with the same name in different folders silently overwrite each other and one package disappears. Packages in a subfolder keep their full names (`living_room/living_room_remote.yaml`, not `living_room/remote.yaml`).
- `packages/.lights/*.yaml` are generated by the Jinja in their header comments. Never edit, reformat or migrate them: they intentionally keep `service:` and have no `default_entity_id`. `packages/light_targets.yaml` includes them with `template: !include_dir_merge_list .lights`.
- Some packages intentionally rely on UI helpers. They're listed in each package's header comment and should stay in the UI (e.g. the derivative helper `sensor.master_bathroom_humidity_change` used by `master_bathroom_humidity`).
- Start every package with a short description (one or two comment lines) of what the package does, followed by a header comment listing its entities by `entity_id`:
  ```yaml
  # Turns the master bathroom fan on when a shower raises the humidity
  # and off again once the humidity settles.
  #
  # External entities used:
  #   Xiaomi BLE (xiaomi_ble)
  #     Master Bathroom: LYWSDCGQ (C4B9) (496303931d7efbad6a29b98ef9ec9871)
  #       sensor.master_bathroom_lywsdcgq_humidity
  #   Derivative helper (derivative, UI)
  #     sensor.master_bathroom_humidity_change
  #   template/some_file.yaml
  #     sensor.some_template_sensor
  #
  # Unused (but related) entities:
  #   Trend helper (trend, UI)
  #     binary_sensor.some_trend_sensor
  #
  # Entities created by this package:
  #   sensor.some_filter_sensor
  #   binary_sensor.some_template_sensor
  ```
  - External entities are those defined outside the package. Group them by the integration that creates them, shown as its display name with the domain in parentheses. Add `UI` when the entity is a helper or config entry created from the UI.
  - Under an integration, list each device as `<Area>: <name_by_user>` (falling back to the device's `name` when `name_by_user` is empty), with its `device_id` in parentheses, so the entities can be found in the UI. Use `No area` when the device has no area. Actions that belong to a device but aren't entities (e.g. `notify.mobile_app_*`) go under that device, marked `(notify action, not an entity)`. List that device's entities under it. Entities that have no device go directly under the integration.
  - Entities defined in YAML elsewhere in the repo are grouped by the file that defines them.
  - Get names, integrations and `device_id`s from `.storage/core.device_registry`, `.storage/core.entity_registry` and `.storage/core.config_entries`. Use them only to read; never edit them.
  - Entities that the package doesn't reference but that relate to it (e.g. leftover UI helpers built on the package's sensors) go in an "Unused (but related) entities" group, using the same grouping. Keep them; don't delete the helpers.
  - Entities created by this package are listed by their real `entity_id` from the entity registry, not one guessed from the name. Leave out automations; they aren't referenced by `entity_id`.
- Shared plumbing stays shared, in its own packages under `packages/shared/` (not copied into the features that use it). For example, "Events - Forward Reload Templates" fires `templates_reloaded`, which is used by both `master_bathroom_humidity` and `holiday_lighting`.
- Check that the package filename doesn't clash with an existing package anywhere under `packages/`, subfolders included.
- Name the package after what it does, matching its description (e.g. `garage_parking_laser`, not `laser`). The candidate names below are only labels.
- Record any problems you notice (bugs, leftover entities, legacy syntax outside the change) under [Known issues](#known-issues) instead of fixing them.
- Afterwards: run a config check, then reload the affected domains. Restart instead if the package includes non-reloadable config (e.g. `sensor:` platforms or `plant:`).

### Candidates

Goal: migrate everything left in `automation/`, `scripts/`, `template/` and `command_line/`, plus `sensor.yaml`, `media_player.yaml`, `notify.yaml`, `compensation.yaml` and `intent_script.yaml`. Delete each file (and its `configuration.yaml` line) once it's empty. These stay where they are: the UI-managed `automations.yaml`, `scripts.yaml` and `scenes.yaml`, and the dashboards (`lovelace`). The infrastructure configs (`cloud`, `logger`, `recorder`, `system_log`, `door_buddy`) were later moved to `packages/system/` and `packages/doors.yaml`. Items marked ⚠ use non-reloadable platforms: do them last and restart once.

Into existing packages:
- [x] doorbell: "Fix Doorbell Chime Status" (automation/reactions.yaml)
- [x] device_firmware_updates: script.update_zwave (scripts/zwave_js.yaml)
- [x] power_outage_shutdown: UPS Model and UPS Battery Runtime (template/system.yaml)
- [x] living_room/living_room_yamaha: Living Room and Dining Room Speakers (media_player.yaml), the receiver volume compensations (compensation.yaml), the living room multizone_controller sensor (sensor.yaml) ⚠

Shared plumbing (packages/shared/):
- [x] notifications: script.notify (scripts/notifiers.yaml) and the notify groups (notify.yaml)
- [x] mqtt_discovery_helpers: scripts/mqtt.yaml
- [x] template_reload_event: "Events - Forward Reload Templates" (automation/events.yaml)

New packages:
- [x] outdoor_sunset_lighting: script.sunrise_sunset (scripts/sunset_sunrise.yaml), "Outdoor Lights On at Sunset, Off at Sunrise" (automation/timed_events.yaml), "Keep Sunset Switches On." (automation/reactions.yaml)
- [x] daylight_saving_reminders: template/daylight_savings_time.yaml and "Notify DST Change" (automation/timed_events.yaml)
- [x] household_reminders: "Notify Change Filters Message" and "Notify Mosby Heartworm and Flee Medication." (automation/timed_events.yaml)
- [x] thermostat_schedule: "Simple Thermostat" (automation/timed_events.yaml)
- [x] server_health: Disk Use Total and Memory Use Total (template/system.yaml), CPU Temperature (command_line/temperature.yaml) ⚠, template/homeassistant_image.yaml, "Notify Snapshot status" and "Clear persistent_notifications at bedtime" (automation/timed_events.yaml)
- [x] living_room/living_room_controllers: "Living Room Scene Controller" and its LEDs (automation/buttons.yaml), "Cube Actions" (automation/cube.yaml), "Living Room Lamp Availability." (automation/reactions.yaml; the commented-out "Fix Wled Errors" copy left in that file was deleted with it)
- [x] zigbee_button_toggles: "Zigbee Button Toggler" (automation/buttons.yaml)
- [x] linked_light_switches: automation/toggles.yaml
- [x] garage_doors: template/door.yaml and script.garage_door_toggle (scripts/nfc.yaml)
- [x] home_occupancy: template/people_tracker.yaml and template/network.yaml
- [x] work_hours_tracking: Petro/Lambo at Work history_stats (sensor.yaml) ⚠ and template/time.yaml
- [x] bonus_room_television: template/bonus_room.yaml and the Bonus Room Television universal player (media_player.yaml) ⚠
- [x] outdoor_weather_station: template/temperatures.yaml
- [x] energy_tariff: template/energy.yaml
- [x] aurora_alerts: automation/aurora.yaml
- [x] drink_tracker: automation/drinks.yaml
- [x] body_weight_tracking: automation/weight.yaml
- [x] awtrix_announcements: scripts/awtrix.yaml
- [x] dashboard_helpers: script.lovelace_toggle (scripts/misc.yaml)
- [x] voice_intents: deleted instead of migrated. intent_script.yaml (git-ignored) held old Alexa custom-skill intents that nothing could reach any more (no top-level `alexa:` config, no custom sentences); it was removed with the git-ignored `alexa/` skill files.
- [x] testing_sandbox: scripts/tests.yaml and "MSR 2 Testing" (automation/apollo_msr2.yaml)
- [x] sensor_calibration_helper: automation/calibrations.yaml (migrated as-is; see Known issues)

Done:
- [x] master bathroom humidity / shower fan (packages/master_bathroom_humidity.yaml)
- [x] doorbell (packages/doorbell.yaml)
- [x] update (packages/device_firmware_updates.yaml)
- [x] laser (packages/garage_parking_laser.yaml; also includes template/garage.yaml)
- [x] basement humidity (packages/basement_humidity_alert.yaml)
- [x] hyperion (packages/tv_ambient_lighting.yaml)
- [x] laundry (packages/laundry_monitor.yaml; also includes the laundry blocks from template/energy.yaml)
- [x] ups (packages/power_outage_shutdown.yaml)
- [x] todo (packages/daily_todo_lists.yaml)
- [x] lzw45 (packages/lzw45_led_strips.yaml; also includes the Mood Lighting switch from template/living_room_remote.yaml)
- [x] run_schedule (packages/running_training_programs.yaml)
- [x] holiday (packages/holiday_lighting.yaml; also includes template/seasons.yaml and the Indoor Holiday switch from template/wled_ambiance.yaml). Later split into `packages/holiday/`: `holiday_lighting.yaml` (the shared holiday logic), `holiday_christmas.yaml` (the Christmas-only lights, front trees and Christmas bulb scene) and `holiday_scenes.yaml` (the other holidays' bulb scenes, from scenes.yaml). Other holidays can get their own files once they have enough devices of their own.
- [x] irrigation (packages/irrigation_scheduler.yaml)
- [x] harmony (packages/living_room/: living_room_harmony.yaml, living_room_remote.yaml and living_room_yamaha.yaml; also includes harmony_helper.yaml, scripts/cast.yaml, template/living_room_remote.yaml, template/yamaha.yaml, template/cast_workout.yaml and the Play/Pause lighting automation from automation/reactions.yaml)
- [x] basement receiver (packages/basement_yamaha.yaml; also includes the yamaha platform and the Deck/Basement Speakers from media_player.yaml, the basement multizone_controller sensor from sensor.yaml, and the Basement Yamaha Receiver sensor from packages/living_room/living_room_yamaha.yaml)
- [x] events (packages/calendar_and_milestone_events.yaml; also includes script.event and script.events from scripts/notifiers.yaml)
- [x] wled (packages/kitchen_cabinet_lighting.yaml, with the cabinet sync automation from automation/toggles.yaml; Movie Time moved to living_room_remote, Front Trees to holiday_lighting, now packages/holiday/holiday_christmas.yaml; the unused scripts/wled.yaml scripts were deleted)
- [x] lighting (packages/light_targets.yaml with the scripts from scripts/lights.yaml and the Fix Zwave Multicast Errors automation from automation/reactions.yaml; the generated template lights are in packages/.lights/)
- [x] house humidity (packages/house_climate.yaml; also includes House Temperature from template/temperatures.yaml)
- [x] echos/alexa (packages/echo_announcements.yaml with the MQTT Discovery automation from automation/echos.yaml and the scripts from scripts/alexa.yaml)
- [x] plants (packages/plant_care_notifications.yaml with the `plant:` config from plants.yaml, automation/plants.yaml and template/plants.yaml)

## Known issues

Problems found while adding package notes, moving packages or updating legacy keys. They're recorded here so they can be fixed later, each as its own change. Don't fix them as part of other work. Add new findings as you go, and remove an entry once the user has had it fixed.

### packages/lzw45_led_strips.yaml
- The LZW45 strips are expected to be removed. When they are, delete this package and its 19 UI helpers (listed in the header), and remove `switch.lzw45_mood_lighting` from `packages/system/system_cloud.yaml` and the recorder `exclude:` list in `packages/system/system_recorder.yaml`, the Mood Lighting dashboard view (`lovelace/views/mood_lighting.yaml`), and the strip lights from `packages/zigbee_button_toggles.yaml` (`light.workshop_bench_strip`) and `lovelace/views/master.yaml`.

### packages/plant_care_notifications.yaml
- Kitty's plant sensor (Xiaomi BLE "Plant Sensor (4C86)", MAC C4:7C:8D:6B:4C:86) is dead: its battery slot corroded, so it needs a replacement sensor. Until then `plant.kitty` stays `unknown`. A new sensor has a new MAC, so its entities get new IDs: either rename them to `sensor.plant_sensor_3_*` in the UI or update the `kitty:` sensors under `plant:` in the package (and its header), then delete the old 4C86 device. Set the new device's area to Dining Room (the old one is wrongly in Game Room). It reports through the dining room ESP32 Bluetooth proxy.

### packages/sensor_calibration_helper.yaml
- Keep this package: it's the user's reusable tool for calibrating any temperature/humidity sensor added to the house (it's normally off between calibrations). Update it before the next use: it still points at the last calibration's sensors. The sensors being calibrated, `sensor.basement_bme280_temperature` / `sensor.basement_bme280_humidity`, belong to the disabled ESPHome "Basement Esp32" config entry, and the reference sensors were renamed: `sensor.apollo_air_1_1ecac0_sen55_temperature` / `_sen55_humidity` are now `sensor.apollo_air_1_1ecac0_temperature` / `sensor.apollo_air_1_1ecac0_humidity`.

### packages/basement_yamaha.yaml
- `switch.basement_bluetooth` is broken (the switch died; a replacement is planned). Until it's replaced, the Echo (Deck) and Echo (Basement) switches can't turn on. When it's replaced, keep the same entity ID or update the 2 switches.

### Xiaomi BLE CGDK2 sensors (removed until HA 2026.12)
- There's a known Xiaomi BLE problem with CGDK2 sensors; they should be discoverable again in HA 2026.12 (December 2026). On 2026-11-15 the user removed all three from the Xiaomi BLE integration: CGDK2 (BC8A) in the Bonus Bedroom (it had just got a new battery), CGDK2 (BCC2) and CGDK2 (BC7C). Until then these entities don't exist: `sensor.bonus_room_cgdk2_*`, `sensor.server_room_cgdk2_*` and `sensor.car_bays_xiaomi_ble_cgdk2_signal_strength`.
- Their registry entries are kept as deleted entities with their old IDs (and the bonus room temperature/humidity keep the `house_climate` label), so HA should restore them when the devices are rediscovered. After upgrading to 2026.12, re-add them and check: the IDs came back unchanged, `sensor.bonus_room_cgdk2_temperature` / `_humidity` still have the `house_climate` label (`packages/house_climate.yaml` averages them), and the dashboards that show them work (`lovelace/views/master.yaml`, `lovelace/views/status_master.yaml`). Set the bonus room device's area to Bonus Bedroom if it doesn't come back.
- Separate from these: the basement CGDK2's Xiaomi BLE entities (`sensor.xiaomi_ble_basement_cgdk2_*`) were deleted on 2026-09-18. It was then read through ESPHome (`sensor.basement_cgdk2_*`), but those entities belong to the "Basement Esp32" ESPHome config entry, which is disabled, so the basement CGDK2 isn't reporting either.

### Dashboards (lovelace/)
- `lovelace/views/dynamic_view_builder.yaml`: the `label` includes use `'..templates/headers/label.yaml'` and `'..templates/headers/label_dynamic.yaml'`, which are missing the `/` after `..`. This only matters when a view passes `label`.
- `lovelace/views/dynamic_view_builder.yaml`: in the `card()` macro, `'entity' not in kwargs` tests a list of `(key, value)` pairs, so it's always true and `entities` is always appended to header cards. It's probably harmless, but it doesn't do what it looks like.
- `lovelace/views/master.yaml`: the Music button's icon is `mdi:mdi:music-box`.
- `lovelace/views/master.yaml`: the area `'Guest Bathoom'` is misspelled. Fixing it changes the view path from `guest_bathoom` to `guest_bathroom`.
- `lovelace/views/master.yaml`: `testing` is never set, so the Testing button never renders. This may be intentional.
