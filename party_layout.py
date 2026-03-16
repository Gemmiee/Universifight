import pygame

# default layout
PARTY_SLOTS = [(310, 250), (215, 260), (130, 260), (50, 260)]

# last saved layout between scenes
_LAST_LAYOUT = None

def _alive_order(hero_list):
    # preserve original order attribute if present; else by list order
    return sorted([h for h in hero_list if getattr(h, "alive", True)],
                  key=lambda h: getattr(h, "order", 0))

def save_party_layout(hero_list):
    """Capture current layout (order + targets) so next scene can restore it."""
    global _LAST_LAYOUT
    data = []
    for h in hero_list:
        tgt = getattr(h, "target", None)
        if tgt is None:
            tgt = pygame.math.Vector2(h.rect.center)
        data.append({
            "name": h.name,
            "order": getattr(h, "order", 0),
            "alive": getattr(h, "alive", True),
            "target": (float(tgt.x), float(tgt.y)),
            "pos": (float(h.rect.centerx), float(h.rect.centery)),
        })
    _LAST_LAYOUT = data

def restore_party_layout(hero_list, fallback_slots=PARTY_SLOTS):
    """
    Apply last saved layout. If none saved yet, fall back to default formation.
    """
    global _LAST_LAYOUT
    if not _LAST_LAYOUT:
        # first scene: apply default formation epeidh den ypraxei akoma battle
        for i, h in enumerate(hero_list):
            h.order = i
            h.target = pygame.math.Vector2(fallback_slots[i])
            h.rect.center = fallback_slots[i]
        return


    by_name = {d["name"]: d for d in _LAST_LAYOUT}
    # Keep heroes in saved order
    hero_list.sort(key=lambda h: by_name.get(h.name, {"order": getattr(h, "order", 0)})["order"])

    for i, h in enumerate(hero_list):
        saved = by_name.get(h.name)
        if saved:
            h.order = saved["order"]
            # keep alive state
            tgt = pygame.math.Vector2(saved["target"])
            h.target = tgt
            h.rect.center = saved["pos"]
        else:
            # Revived? Drop them into the next slot
            h.order = i
            h.target = pygame.math.Vector2(fallback_slots[min(i, len(fallback_slots)-1)])
            h.rect.center = tuple(h.target)

def freeze_targets_at_current(hero_list):
    """after victory, pin targets to current positions so nothing snaps back."""
    for h in hero_list:
        if getattr(h, "alive", True):
            h.target = pygame.math.Vector2(h.rect.center)

def reflow_alive_into_front(hero_list, fallback_slots=PARTY_SLOTS):
    alive = _alive_order(hero_list)
    for i, h in enumerate(alive):
        h.target = pygame.math.Vector2(fallback_slots[i])
