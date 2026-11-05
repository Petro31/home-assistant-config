```
{%- set ns = namespace(device=[], entity=[]) %}
{%- for s in states %}
  {%- set e = s.entity_id %}
  {%- set a = e | area_name %}
  {%- set d = e | device_name %}
  {%- set n = e | entity_name %}
  {%- set n2 = e | entity_name(fallback=True) %}
  {%- set did = e | device_id %}
  {%- if a and d and a in d %}
    {%- set ns.device = ns.device + [dict(id=did, e=e, a=a, d=d, n=n, n2=n2)] %}
  {%- endif %}
  {% if d and n and n2 and d in n and d != n2 %}
    {%- set ns.entity = ns.entity + [dict(id=did, e=e, a=a, d=d, n=n, n2=n2)] %}
  {% endif %}
{%- endfor %}
Remove area from devices

Area | Device Name | New Name
:-:|:-:|:-:
{%- for did, items in ns.device | groupby('id') %}
{%- set a = items | map(attribute='a') | unique | first  %}
{%- set d = items | map(attribute='d') | unique | first  %}
{{ a }} | {{ d }} | {{ d.replace(a, "").strip() }}
{%- endfor %}
```


Area | Device Name | New Name
:-:|:-:|:-:
Back Yard | Back Yard Sprinker Cycle | Sprinker Cycle
Basement | Basement Recessed Switch | Recessed Switch
Basement | Echo Basement | Echo
Deck | Deck Camera | Camera
Deck | Deck Fan 1 | Fan 1
Deck | Deck Fan 2 | Fan 2
Deck | Deck Mood Lighting | Mood Lighting
Deck | Deck Motion Sensor | Motion Sensor
Deck | Deck Recessed Dimmer | Recessed Dimmer
Deck | Deck Uplights | Uplights
Deck | Deck Walkway Lights | Walkway Lights
Deck | Deck WLED | WLED
Dining Room | Dining Room Chandelier Switch | Chandelier Switch
Dining Room | Dining Room Esp32 | Esp32
Dining Room | Dining Room Uplight 1 | Uplight 1
Dining Room | Dining Room Uplight 2 | Uplight 2
Foyer | Foyer Camera | Camera
Foyer | Foyer Switch | Switch
Front Yard | Front Yard Sprinker Cycle | Sprinker Cycle
Front Yard | Front Yard Uplight Left | Uplight Left
Front Yard | Front Yard Uplight Middle | Uplight Middle
Front Yard | Front Yard Uplight Right | Uplight Right
Game Room | Echo Game Room | Echo
Game Room | Game Room Bookcase Outlet | Bookcase Outlet
Game Room | Game Room Buffet Outlet | Buffet Outlet
Game Room | Game Room Esp32 | Esp32
Game Room | Game Room Switch | Switch
Game Room | Game Room Window Outlet Switch | Window Outlet Switch
Hallway | Hallway Switch | Switch
Kitchen | Echo Kitchen | Echo
Kitchen | Kitchen Camera | Camera
Kitchen | Kitchen Esp32 | Esp32
Kitchen | Kitchen Island Dimmer | Island Dimmer
Kitchen | Kitchen Outlet Above The Microwave Switch | Outlet Above The Microwave Switch
Kitchen | Kitchen Outlet Above The Refrigerator Switch | Outlet Above The Refrigerator Switch
Kitchen | Kitchen Recessed Lights Switch | Recessed Lights Switch
Kitchen | Kitchen Sink | Sink
Laundry Room | Laundry Room Light Switch | Light Switch
Living Room | Echo Living Room | Echo
Living Room | Living Room Outlet Switch | Outlet Switch
Living Room | Living Room Roku | Roku
Living Room | Living Room Scene Controller | Scene Controller
Living Room | Living Room Scene Controller 2 | Scene Controller 2
Living Room | Living Room Thermostat | Thermostat
Living Room | Living Room TV | TV
Living Room | Living Room Uplight | Uplight
Master Bathroom | Master Bathroom Recessed Light Switch | Recessed Light Switch
Master Bathroom | Master Bathroom Vanity Light Switch | Vanity Light Switch
Master Bedroom | Master Bedroom Fan | Fan
Master Bedroom | Master Bedroom Fan Light Switch | Fan Light Switch
Master Bedroom | Master Bedroom Lindsay's Nightstand | Lindsay's Nightstand
Master Bedroom | Master Bedroom Mike's Nightstand | Mike's Nightstand
Master Closet | Master Closet Esp32 | Esp32
Office | Bonus Room Office Fan | Bonus Room  Fan
Office | Bonus Room Office Fan Light Switch | Bonus Room  Fan Light Switch
Office | Bonus Room Office Lights | Bonus Room  Lights
Office | Office 8 Port Switch | 8 Port Switch
Office | Office Bluetooth Proxy | Bluetooth Proxy
Office | Office D1 Mini | D1 Mini
Office | Office Flex Mini | Flex Mini
Porch | Porch Outlet Switch | Outlet Switch
Powder Room | Powder Room Sink | Sink
Server Room | Server Room 16 Port POE Switch | 16 Port POE Switch
Server Room | Server Room AC Lite | AC Lite
Server Room | Server Room Door | Door
Server Room | Server Room Gateway Pro | Gateway Pro
Server Room | Server Room Switch | Switch
Workshop | Workshop Light Switch | Light Switch