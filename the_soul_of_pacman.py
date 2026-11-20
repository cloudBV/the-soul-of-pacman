import asyncio
import pygame
import sys
import random
import math
from collections import deque

# ── constants ──────────────────────────────────────────────────────────────────
CELL         = 28
COLS         = 29
ROWS         = 23
W            = COLS * CELL
H            = ROWS * CELL + 80

TRANSFER_STEPS = 10
CORPSE_TURNS   = 5
FLEE_RADIUS    = 8
BLAST_RADIUS   = 5

FPS = 60

PAC_MOVE_INTERVAL = 200
AI_GHOST_INTERVAL = 300
PLAYER_GHOST_INTERVAL = 150

TRANSFER_WARNING_STEPS = 4
SWITCH_PENALTY = 300

SHAKE_FRAMES = 6
SHAKE_INTENSITY = 4

COMBO_TIMEOUT = 180
COMBO_MULTIPLIER = 100

BG        = (10,  10,  30)
WALL_COL  = (20,  45, 130)
WALL_INNER = (35, 60, 160)
DOT_COL   = (255, 210,  50)
HUD_BG    = (6,   6,   18)
WHITE     = (255, 255, 255)
GRAY      = (100, 100, 115)
PAC_COL   = (255, 225,  40)
WARNING_COL = (255, 100, 100)
BLAST_COL = (255, 200, 50)

GHOST_COLS = [
    (255,  65,  65),
    (255, 155,  35),
    ( 50, 205, 255),
    (255, 120, 215),
    (140, 255, 140),
]

GHOST_PERSONALITIES = ['aggressive', 'patrol', 'ambush', 'random']

DIRS4 = [(-1,0),(1,0),(0,-1),(0,1)]

MAZE_LAYOUT = [
    [0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0],
    [0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0],
    [0,0,1,1,0,0,0,0,1,1,0,0,0,0,0,0,0,0,1,1,0,0,0,0,1,1,0,0,0],
    [0,0,1,1,0,0,0,0,1,1,0,0,0,0,0,0,0,0,1,1,0,0,0,0,1,1,0,0,0],
    [0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0],
    [0,0,0,0,0,0,0,0,0,0,0,0,0,1,1,0,0,0,0,0,0,0,0,0,0,0,0,0,0],
    [0,0,0,0,0,0,0,1,1,0,0,0,0,1,1,0,0,0,0,1,1,0,0,0,0,0,0,0,0],
    [0,0,1,1,0,0,0,1,1,0,0,0,0,0,0,0,0,0,0,1,1,0,0,0,1,1,0,0,0],
    [0,0,1,1,0,0,0,1,1,0,0,0,0,0,0,0,0,0,0,1,1,0,0,0,1,1,0,0,0],
    [0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0],
    [0,0,0,0,0,0,0,0,0,0,0,0,0,1,1,0,0,0,0,0,0,0,0,0,0,0,0,0,0],
    [0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0],
    [0,0,0,0,0,0,0,0,0,0,0,0,0,1,1,0,0,0,0,0,0,0,0,0,0,0,0,0,0],
    [0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0],
    [0,0,1,1,0,0,0,1,1,0,0,0,0,0,0,0,0,0,0,1,1,0,0,0,1,1,0,0,0],
    [0,0,1,1,0,0,0,1,1,0,0,0,0,0,0,0,0,0,0,1,1,0,0,0,1,1,0,0,0],
    [0,0,0,0,0,0,0,1,1,0,0,0,0,1,1,0,0,0,0,1,1,0,0,0,0,0,0,0,0],
    [0,0,0,0,0,0,0,0,0,0,0,0,0,1,1,0,0,0,0,0,0,0,0,0,0,0,0,0,0],
    [0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0],
    [0,0,1,1,0,0,0,0,1,1,0,0,0,0,0,0,0,0,1,1,0,0,0,0,1,1,0,0,0],
    [0,0,1,1,0,0,0,0,1,1,0,0,0,0,0,0,0,0,1,1,0,0,0,0,1,1,0,0,0],
    [0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0],
    [0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0]
]

def in_bounds(r, c):
    return 0 <= r < ROWS and 0 <= c < COLS

def is_wall(r, c):
    if r == 0 or r == ROWS-1 or c == 0 or c == COLS-1:
        return True
    return MAZE_LAYOUT[r][c] == 1

def passable(r, c):
    return in_bounds(r, c) and not is_wall(r, c)

def manhattan(r1,c1,r2,c2):
    return abs(r1-r2)+abs(c1-c2)

def bfs_next(sr, sc, tr, tc, avoid=()):
    if sr==tr and sc==tc: return (0,0)
    avoid = set(avoid)
    q = deque([(sr,sc,None)])
    seen = {(sr,sc)}
    while q:
        r,c,first = q.popleft()
        for dr,dc in DIRS4:
            nr,nc = r+dr,c+dc
            if (nr,nc) in seen or not passable(nr,nc) or (nr,nc) in avoid:
                continue
            seen.add((nr,nc))
            step = first or (dr,dc)
            if nr==tr and nc==tc: return step
            q.append((nr,nc,step))
    return None

def bfs_dist_map(sr, sc, blocked=set()):
    dist = {(sr,sc): 0}
    q = deque([(sr,sc)])
    while q:
        r,c = q.popleft()
        for dr,dc in DIRS4:
            nr,nc = r+dr,c+dc
            if (nr,nc) not in dist and passable(nr,nc) and (nr,nc) not in blocked:
                dist[(nr,nc)] = dist[(r,c)] + 1
                q.append((nr,nc))
    return dist

def nearest_dot_pos(grid, r, c):
    q = deque([(r,c)])
    seen = {(r,c)}
    while q:
        cr,cc = q.popleft()
        if grid[cr][cc] == 1 and (cr != r or cc != c):
            return (cr,cc)
        for dr,dc in DIRS4:
            nr,nc = cr+dr,cc+dc
            if (nr,nc) not in seen and passable(nr,nc):
                seen.add((nr,nc))
                q.append((nr,nc))
    return None

# ── particles ──────────────────────────────────────────────────────────────────
def spawn_blast_particles(s, r, c):
    if len(s['particles']) > 60:
        return
    for _ in range(15):
        angle = random.uniform(0, 2 * math.pi)
        speed = random.uniform(2, 6)
        s['particles'].append({
            'x': c * CELL + CELL//2,
            'y': r * CELL + CELL//2,
            'vx': math.cos(angle) * speed,
            'vy': math.sin(angle) * speed,
            'life': random.randint(10, 25),
            'color': random.choice([BLAST_COL, PAC_COL, WHITE]),
            'size': random.randint(2, 5),
        })

def update_particles(s):
    for p in s['particles'][:]:
        p['x'] += p['vx']
        p['y'] += p['vy']
        p['life'] -= 1
        if p['life'] <= 0:
            s['particles'].remove(p)

def draw_particles(surf, s):
    for p in s['particles']:
        alpha = int(255 * (p['life'] / 25))
        color = p['color'] + (alpha,) if len(p['color']) == 3 else p['color']
        pygame.draw.circle(surf, color[:3], (int(p['x']), int(p['y'])), p['size'])

# ── pac-man AI ─────────────────────────────────────────────────────────────────
def pacman_step(pac, ghosts, grid):
    pr,pc = pac['r'],pac['c']
    ghost_positions = {(g['r'],g['c']) for g in ghosts}
    
    all_moves = [(dr,dc) for dr,dc in DIRS4 if passable(pr+dr,pc+dc)]
    if not all_moves:
        return
    
    safe_moves = [(dr,dc) for dr,dc in all_moves 
                  if (pr+dr, pc+dc) not in ghost_positions]
    if not safe_moves:
        return
    
    open_moves = safe_moves
    min_ghost_dist = min(manhattan(pr,pc,g['r'],g['c']) for g in ghosts) if ghosts else 99

    if min_ghost_dist <= FLEE_RADIUS:
        best_move = None
        best_score = -99999
        ghost_dist_maps = [bfs_dist_map(g['r'], g['c']) for g in ghosts]
        
        for dr, dc in open_moves:
            nr, nc = pr+dr, pc+dc
            score = sum(dm.get((nr,nc), 0) for dm in ghost_dist_maps)
            if grid[nr][nc] == 1:
                score += 5
            if dr == -pac.get('dr', 0) and dc == -pac.get('dc', 0):
                score -= 10
            if score > best_score:
                best_score = score
                best_move = (dr, dc)
        step = best_move
    else:
        target = nearest_dot_pos(grid, pr, pc)
        if target:
            step = bfs_next(pr, pc, target[0], target[1], avoid=ghost_positions)
            if step is None:
                best_move = None
                best_dist = 99999
                for dr, dc in open_moves:
                    nr, nc = pr+dr, pc+dc
                    alt_target = nearest_dot_pos(grid, nr, nc)
                    if alt_target:
                        dist = manhattan(nr, nc, alt_target[0], alt_target[1])
                        if dist < best_dist:
                            best_dist = dist
                            best_move = (dr, dc)
                step = best_move
        else:
            step = None

    if step is None:
        non_reverse = [(dr,dc) for dr,dc in open_moves 
                      if (dr != -pac.get('dr', 0) or dc != -pac.get('dc', 0))]
        step = random.choice(non_reverse) if non_reverse else random.choice(open_moves)

    if step:
        dr, dc = step
        nr, nc = pr+dr, pc+dc
        
        if (nr, nc) in {(g['r'],g['c']) for g in ghosts}:
            emergency = [(ddr,ddc) for ddr,ddc in open_moves 
                        if (pr+ddr, pc+ddc) not in {(g['r'],g['c']) for g in ghosts}]
            if emergency:
                dr, dc = random.choice(emergency)
                nr, nc = pr+dr, pc+dc
            else:
                return
        
        pac['r'], pac['c'] = nr, nc
        pac['dr'], pac['dc'] = dr, dc
        pac['steps'] += 1
        
        if grid[nr][nc] == 1:
            grid[nr][nc] = 2
            pac['dots_eaten'] += 1

# ── AI ghost movement with personalities ──────────────────────────────────────
def ai_ghost_step(ghost, pac, all_ghosts, grid):
    gr, gc = ghost['r'], ghost['c']
    pr, pc = pac['r'], pac['c']
    personality = GHOST_PERSONALITIES[ghost['id'] % len(GHOST_PERSONALITIES)]
    
    other_positions = {(g['r'], g['c']) for g in all_ghosts if g is not ghost}
    
    valid_moves = []
    for dr, dc in DIRS4:
        nr, nc = gr+dr, gc+dc
        if passable(nr, nc) and (nr, nc) not in other_positions:
            valid_moves.append((dr, dc))
    
    if not valid_moves:
        return
    
    current_dist = manhattan(gr, gc, pr, pc)
    
    if personality == 'aggressive':
        if random.random() < 0.9:
            step_to_pac = bfs_next(gr, gc, pr, pc, avoid=other_positions)
            if step_to_pac and step_to_pac != (0,0):
                dr, dc = step_to_pac
                nr, nc = gr+dr, gc+dc
                if passable(nr, nc) and (nr, nc) not in other_positions:
                    move_ghost(ghost, nr, nc, dr, dc, grid)
                    return
        best_move = min(valid_moves, key=lambda m: manhattan(gr+m[0], gc+m[1], pr, pc))
    
    elif personality == 'patrol':
        if current_dist < 5:
            step_to_pac = bfs_next(gr, gc, pr, pc, avoid=other_positions)
            if step_to_pac and step_to_pac != (0,0):
                dr, dc = step_to_pac
                nr, nc = gr+dr, gc+dc
                if passable(nr, nc) and (nr, nc) not in other_positions:
                    move_ghost(ghost, nr, nc, dr, dc, grid)
                    return
            best_move = min(valid_moves, key=lambda m: manhattan(gr+m[0], gc+m[1], pr, pc))
        else:
            if random.random() < 0.7:
                dr, dc = ghost.get('dr', 0), ghost.get('dc', 1)
                if (dr, dc) in valid_moves:
                    best_move = (dr, dc)
                else:
                    best_move = random.choice(valid_moves)
            else:
                best_move = random.choice(valid_moves)
    
    elif personality == 'ambush':
        target_r = pr + pac.get('dr', 0) * 4
        target_c = pc + pac.get('dc', 0) * 4
        if passable(target_r, target_c):
            step = bfs_next(gr, gc, target_r, target_c, avoid=other_positions)
            if step and step != (0,0):
                dr, dc = step
                nr, nc = gr+dr, gc+dc
                if passable(nr, nc) and (nr, nc) not in other_positions:
                    move_ghost(ghost, nr, nc, dr, dc, grid)
                    return
        best_move = min(valid_moves, key=lambda m: manhattan(gr+m[0], gc+m[1], pr, pc))
    
    else:
        if random.random() < 0.4:
            best_move = min(valid_moves, key=lambda m: manhattan(gr+m[0], gc+m[1], pr, pc))
        else:
            best_move = random.choice(valid_moves)
    
    dr, dc = best_move
    nr, nc = gr+dr, gc+dc
    move_ghost(ghost, nr, nc, dr, dc, grid)

def move_ghost(ghost, nr, nc, dr, dc, grid):
    ghost['r'], ghost['c'] = nr, nc
    ghost['dr'], ghost['dc'] = dr, dc
    if grid[nr][nc] == 1:
        grid[nr][nc] = 2

# ── soul transfer ──────────────────────────────────────────────────────────────
def try_soul_transfer(s):
    if not s['ghosts']:
        return False

    pac = s['pac']
    pac_old_pos = (pac['r'], pac['c'])
    
    farthest_idx = max(
        range(len(s['ghosts'])),
        key=lambda i: manhattan(s['ghosts'][i]['r'], s['ghosts'][i]['c'], pac['r'], pac['c'])
    )
    farthest_dist = manhattan(
        s['ghosts'][farthest_idx]['r'], s['ghosts'][farthest_idx]['c'], pac['r'], pac['c']
    )

    if farthest_dist <= 3:
        return False

    ghost_to_possess = s['ghosts'][farthest_idx]
    
    pac_corpse = {
        'r': pac_old_pos[0],
        'c': pac_old_pos[1],
        'turns_left': CORPSE_TURNS,
        'ghost_id': ghost_to_possess['id'],
        'display_color': PAC_COL,
        'revive_color': ghost_to_possess['color'],
    }
    s['corpses'].append(pac_corpse)
    
    other_ghosts = [(i, g) for i, g in enumerate(s['ghosts']) if i != farthest_idx]
    
    blast_victim_idx = None
    if other_ghosts:
        ghosts_in_range = []
        for i, g in other_ghosts:
            dist = manhattan(pac_old_pos[0], pac_old_pos[1], g['r'], g['c'])
            if dist <= BLAST_RADIUS:
                ghosts_in_range.append((i, dist))
        
        if ghosts_in_range:
            min_dist = min(d for _, d in ghosts_in_range)
            closest = [i for i, d in ghosts_in_range if d == min_dist]
            blast_victim_idx = random.choice(closest)
    
    if blast_victim_idx is not None:
        blast_ghost = s['ghosts'][blast_victim_idx]
        ghost_corpse = {
            'r': blast_ghost['r'],
            'c': blast_ghost['c'],
            'turns_left': CORPSE_TURNS,
            'ghost_id': blast_ghost['id'],
            'display_color': blast_ghost['color'],
            'revive_color': blast_ghost['color'],
        }
        s['corpses'].append(ghost_corpse)
        s['blast_pos'] = (blast_ghost['r'], blast_ghost['c'])
    else:
        s['blast_pos'] = (pac_old_pos[0], pac_old_pos[1])
    
    s['shake_timer'] = SHAKE_FRAMES
    spawn_blast_particles(s, s['blast_pos'][0], s['blast_pos'][1])
    
    s['combo_count'] += 1
    s['combo_timer'] = COMBO_TIMEOUT
    s['score'] += s['combo_count'] * COMBO_MULTIPLIER
    
    s['blast_timer'] = 15
    
    pac['r'], pac['c'] = ghost_to_possess['r'], ghost_to_possess['c']
    pac['dr'], pac['dc'] = ghost_to_possess['dr'], ghost_to_possess['dc']
    
    indices_to_remove = sorted([farthest_idx] + ([blast_victim_idx] if blast_victim_idx is not None else []), reverse=True)
    
    was_player_removed = False
    for idx in indices_to_remove:
        if idx == s['selected']:
            was_player_removed = True
        s['ghosts'].pop(idx)
    
    if was_player_removed or s['selected'] >= len(s['ghosts']):
        s['selected'] = 0 if s['ghosts'] else 0
    
    pac['steps'] = pac['steps'] - (pac['steps'] % TRANSFER_STEPS)
    
    return True

# ── build world ────────────────────────────────────────────────────────────────
def build_grid():
    return [[0 if is_wall(r,c) else 1 for c in range(COLS)] for r in range(ROWS)]

def new_game():
    grid = build_grid()
    total_dots = sum(cell == 1 for row in grid for cell in row)

    corners = [(1,1), (1,COLS-2), (ROWS-2,1), (ROWS-2,COLS-2)]
    ghosts = []
    for i, (r, c) in enumerate(corners):
        if not passable(r, c):
            for dr, dc in DIRS4:
                if passable(r+dr, c+dc):
                    r, c = r+dr, c+dc
                    break
        ghosts.append({
            'r': r, 'c': c,
            'dr': 0, 'dc': 1,
            'id': i,
            'color': GHOST_COLS[i % len(GHOST_COLS)]
        })

    pr, pc = ROWS//2, COLS//2
    if not passable(pr, pc):
        for r in range(ROWS):
            for c in range(COLS):
                if passable(r, c):
                    pr, pc = r, c
                    break
            else:
                continue
            break

    grid[pr][pc] = 2
    pac = {
        'r': pr, 'c': pc,
        'dr': 0, 'dc': 1,
        'steps': 0,
        'dots_eaten': 0
    }

    return {
        'grid':      grid,
        'total_dots': total_dots,
        'ghosts':    ghosts,
        'pac':       pac,
        'corpses':   [],
        'selected':  0,
        'mouth':     True,
        'over':      False,
        'won':       False,
        'show_hint': True,
        'hint_timer': 180,
        'pac_timer': 0,
        'ai_ghost_timer': 0,
        'player_ghost_timer': 0,
        'player_ghost_move_queued': False,
        'player_ghost_move_dir': (0, 0),
        'transfer_warning': False,
        'blast_pos': None,
        'blast_timer': 0,
        'switch_penalty': 0,
        'particles': [],
        'shake_timer': 0,
        'score': 0,
        'combo_count': 0,
        'combo_timer': 0,
    }

# ── drawing ────────────────────────────────────────────────────────────────────
def draw_ghost(surf, gx, gy, color, selected, label, fnt):
    S = CELL - 2
    pad = 1
    surf2 = pygame.Surface((S, S+6), pygame.SRCALPHA)
    cx, cy = S//2, S//3
    r2 = S//2
    pygame.draw.rect(surf2, color+(255,), (0, cy, S, S-cy))
    pygame.draw.circle(surf2, color+(255,), (cx, cy), r2)
    bw = S//3
    pygame.draw.rect(surf2, color+(255,), (0, S-bw//2, S, bw//2))
    for i in range(3):
        bx = i*bw + bw//2
        pygame.draw.circle(surf2, color+(255,), (bx, S), bw//2)
    for ex in (S//3, 2*S//3):
        pygame.draw.circle(surf2, (255,255,255,255), (ex, S//3), max(2,S//8))
        pygame.draw.circle(surf2, (20,20,80,255), (ex+1,S//3), max(1,S//16))
    surf.blit(surf2, (gx+pad, gy+pad-3))
    if selected:
        pygame.draw.rect(surf, WHITE, (gx, gy, CELL, CELL), 2)
    t = fnt.render(label, True, WHITE)
    surf.blit(t, (gx+CELL//2-t.get_width()//2, gy+CELL-2))

def draw_pacman(surf, px, py, dr, dc, mouth_open, warning=False):
    cx = px + CELL//2
    cy = py + CELL//2
    r = CELL//2 - 3
    if dc == 1:   face = 0
    elif dc == -1: face = 180
    elif dr == -1: face = 90
    else:          face = 270
    gap = 28 if mouth_open else 4
    pts = [(cx, cy)]
    for i in range(31):
        a = math.radians(face+gap + (360-2*gap)/30*i)
        pts.append((cx+r*math.cos(a), cy-r*math.sin(a)))
    color = WARNING_COL if warning else PAC_COL
    pygame.draw.polygon(surf, color, pts)

def draw_corpse(surf, gx, gy, turns_left, display_color, fnt):
    cx = gx + CELL//2
    cy = gy + CELL//2
    pygame.draw.circle(surf, display_color, (cx, cy), CELL//2-4)
    pygame.draw.circle(surf, (80,60,20), (cx,cy), CELL//2-4, 1)
    t = fnt.render(str(turns_left), True, WHITE)
    surf.blit(t, (cx-t.get_width()//2, cy-t.get_height()//2))

def draw_blast_effect(surf, r, c, timer):
    cx = c * CELL + CELL//2
    cy = r * CELL + CELL//2
    max_radius = CELL * 3
    progress = timer / 15.0
    radius = int(max_radius * (1.0 - progress))
    alpha = int(255 * progress)
    if radius > 0 and alpha > 0:
        blast_surf = pygame.Surface((radius*2+4, radius*2+4), pygame.SRCALPHA)
        pygame.draw.circle(blast_surf, BLAST_COL + (alpha,), 
                          (radius+2, radius+2), radius, max(1, int(radius*0.3)))
        surf.blit(blast_surf, (cx - radius - 2, cy - radius - 2))

def draw_hud(surf, fnt, fnt_s, s):
    y0 = ROWS*CELL
    pygame.draw.rect(surf, HUD_BG, (0, y0, W, 80))
    pygame.draw.line(surf, (45,80,190), (0,y0), (W,y0), 1)

    dots_left = sum(cell == 1 for row in s['grid'] for cell in row)
    total_dots = s['total_dots']
    pct = (total_dots - dots_left) / max(total_dots, 1) * 100
    
    surf.blit(fnt.render(f"score: {s['score']}", True, WHITE), (12, y0+8))
    
    if s['combo_timer'] > 0 and s['combo_count'] > 0:
        combo_text = f"COMBO x{s['combo_count']}!"
        combo_col = (255, 255, 100) if s['combo_count'] < 3 else (255, 150, 50)
        surf.blit(fnt_s.render(combo_text, True, combo_col), (12, y0+30))
    
    surf.blit(fnt_s.render(f"dots: {dots_left} ({pct:.0f}%)", True, DOT_COL), (12, y0+50))

    steps_mod = s['pac']['steps'] % TRANSFER_STEPS
    steps_until = TRANSFER_STEPS - steps_mod
    bar_w = 140
    bx = W//2 - bar_w//2
    by = y0 + 10
    pygame.draw.rect(surf, (35,35,70), (bx, by, bar_w, 11), border_radius=3)
    fill = int(bar_w * steps_mod / TRANSFER_STEPS)
    
    if steps_until <= TRANSFER_WARNING_STEPS:
        col = (255, 80, 80)
        warning_text = f"⚠ TRANSFER IN {steps_until}! ⚠"
    else:
        col = (80, 180, 255)
        warning_text = f"transfer in {steps_until} steps"
    
    if fill > 0:
        pygame.draw.rect(surf, col, (bx, by, fill, 11), border_radius=3)
    surf.blit(fnt_s.render(warning_text, True, WHITE), (bx+bar_w//2-52, by+13))

    sorted_ghosts = sorted(s['ghosts'], key=lambda g: g['id'])
    gx0 = W - 12 - len(sorted_ghosts)*38
    for display_i, g in enumerate(sorted_ghosts):
        cx = gx0 + display_i*38 + 14
        pygame.draw.circle(surf, g['color'], (cx, y0+22), 12)
        if (s['ghosts'] and s['selected'] < len(s['ghosts']) 
            and g is s['ghosts'][s['selected']]):
            pygame.draw.circle(surf, WHITE, (cx, y0+22), 14, 2)
            label = fnt_s.render("YOU", True, WHITE)
            surf.blit(label, (cx - label.get_width()//2, y0+40))
        else:
            pers = GHOST_PERSONALITIES[g['id'] % len(GHOST_PERSONALITIES)]
            init = pers[0].upper()
            surf.blit(fnt_s.render(init, True, WHITE), (cx-3, y0+40))

    surf.blit(fnt_s.render("1-5=select   TAP arrows=move   R=restart", True, GRAY), (W//2-100, y0+60))

def draw_controls_hint(surf, fnt):
    hint_text = "PRESS 1-4 TO SWITCH GHOST  |  TAP ARROWS TO MOVE!"
    text_surf = fnt.render(hint_text, True, (255, 255, 100))
    text_rect = text_surf.get_rect(center=(W//2, ROWS*CELL//2 - 80))
    bg_rect = text_rect.inflate(20, 10)
    s = pygame.Surface(bg_rect.size, pygame.SRCALPHA)
    s.fill((0, 0, 0, 180))
    surf.blit(s, bg_rect)
    pygame.draw.rect(surf, (255, 255, 100), bg_rect, 2)
    surf.blit(text_surf, text_rect)

def draw_overlay(surf, fb, fm, line1, line2, score=0):
    ov = pygame.Surface((W, ROWS*CELL), pygame.SRCALPHA)
    ov.fill((0,0,0,165))
    surf.blit(ov, (0,0))
    t = fb.render(line1, True, WHITE)
    surf.blit(t, (W//2-t.get_width()//2, ROWS*CELL//2-55))
    t2 = fm.render(line2, True, GRAY)
    surf.blit(t2, (W//2-t2.get_width()//2, ROWS*CELL//2+5))
    if score > 0:
        t3 = fm.render(f"final score: {score}", True, WHITE)
        surf.blit(t3, (W//2-t3.get_width()//2, ROWS*CELL//2+25))

def select_ghost_by_id(s, target_id):
    for i, g in enumerate(s['ghosts']):
        if g['id'] == target_id:
            s['selected'] = i
            return

# ── main ───────────────────────────────────────────────────────────────────────
async def main():
    pygame.init()
    screen = pygame.display.set_mode((W, H))
    pygame.display.set_caption("Haunting Pac-Man - Soul Blast!")
    clock = pygame.time.Clock()

    fb = pygame.font.SysFont("monospace", 40, bold=True)
    fm = pygame.font.SysFont("monospace", 19)
    fs = pygame.font.SysFont("monospace", 13)
    fh = pygame.font.SysFont("monospace", 22, bold=True)

    state = new_game()

    while True:
        dt = clock.tick(FPS)
        s = state

        if s['combo_timer'] > 0:
            s['combo_timer'] -= 1
            if s['combo_timer'] <= 0:
                s['combo_count'] = 0

        if s.get('show_hint') and s.get('hint_timer', 0) > 0:
            s['hint_timer'] -= 1
            if s['hint_timer'] <= 0:
                s['show_hint'] = False

        if s.get('blast_timer', 0) > 0:
            s['blast_timer'] -= 1
        
        if s.get('switch_penalty', 0) > 0:
            s['switch_penalty'] -= dt
        
        update_particles(s)

        steps_until = TRANSFER_STEPS - (s['pac']['steps'] % TRANSFER_STEPS)
        s['transfer_warning'] = steps_until <= TRANSFER_WARNING_STEPS

        shake_x, shake_y = 0, 0
        if s.get('shake_timer', 0) > 0:
            s['shake_timer'] -= 1
            shake_x = random.randint(-SHAKE_INTENSITY, SHAKE_INTENSITY)
            shake_y = random.randint(-SHAKE_INTENSITY, SHAKE_INTENSITY)

        for ev in pygame.event.get():
            if ev.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
            
            if ev.type == pygame.KEYDOWN:
                if ev.key == pygame.K_r:
                    state = new_game()
                    continue
                
                if s['over']:
                    continue

                num_map = {
                    pygame.K_1: 0, pygame.K_2: 1,
                    pygame.K_3: 2, pygame.K_4: 3, pygame.K_5: 4,
                }
                if ev.key in num_map:
                    target = num_map[ev.key]
                    if target < len(s['ghosts']):
                        select_ghost_by_id(s, target)
                        s['switch_penalty'] = SWITCH_PENALTY
                        s['player_ghost_timer'] = 0
                        s['player_ghost_move_queued'] = False
                    continue
                
                if s.get('switch_penalty', 0) > 0:
                    continue
                
                if ev.key in (pygame.K_UP, pygame.K_DOWN, pygame.K_LEFT, pygame.K_RIGHT):
                    dr, dc = 0, 0
                    if ev.key == pygame.K_UP:    dr = -1
                    if ev.key == pygame.K_DOWN:  dr = 1
                    if ev.key == pygame.K_LEFT:  dc = -1
                    if ev.key == pygame.K_RIGHT: dc = 1
                    
                    s['player_ghost_move_queued'] = True
                    s['player_ghost_move_dir'] = (dr, dc)

        if not s['over'] and s['ghosts']:
            s['pac_timer'] += dt
            s['ai_ghost_timer'] += dt
            s['player_ghost_timer'] += dt
            
            ai_interval = AI_GHOST_INTERVAL
            if s['ghosts']:
                pac = s['pac']
                min_ai_dist = min(manhattan(pac['r'], pac['c'], g['r'], g['c']) 
                                 for g in s['ghosts'])
                if min_ai_dist > 10:
                    ai_interval = int(AI_GHOST_INTERVAL * 0.7)
                
            if s['ai_ghost_timer'] >= ai_interval:
                s['ai_ghost_timer'] -= ai_interval
                for i, ghost in enumerate(s['ghosts']):
                    if i != s['selected']:
                        ai_ghost_step(ghost, s['pac'], s['ghosts'], s['grid'])
            
            if (s['player_ghost_move_queued'] and 
                s['player_ghost_timer'] >= PLAYER_GHOST_INTERVAL and
                s.get('switch_penalty', 0) <= 0):
                
                s['player_ghost_timer'] = 0
                s['player_ghost_move_queued'] = False
                
                dr, dc = s['player_ghost_move_dir']
                
                if s['selected'] < len(s['ghosts']):
                    ag = s['ghosts'][s['selected']]
                    nr = ag['r'] + dr
                    nc = ag['c'] + dc
                    
                    other_ghost_positions = {
                        (g['r'], g['c']) 
                        for i, g in enumerate(s['ghosts']) 
                        if i != s['selected']
                    }
                    corpse_positions = {(c['r'], c['c']) for c in s['corpses']}
                    blocked = other_ghost_positions | corpse_positions
                    
                    if passable(nr, nc) and (nr, nc) not in blocked:
                        ag['r'], ag['c'] = nr, nc
                        ag['dr'], ag['dc'] = dr, dc
                        
                        if ag['r'] == s['pac']['r'] and ag['c'] == s['pac']['c']:
                            s['over'] = True
                            s['won'] = True
                        
                        if s['grid'][nr][nc] == 1:
                            s['grid'][nr][nc] = 2
            
            if s['pac_timer'] >= PAC_MOVE_INTERVAL:
                s['pac_timer'] -= PAC_MOVE_INTERVAL
                pacman_step(s['pac'], s['ghosts'], s['grid'])
                s['mouth'] = not s['mouth']
                
                pac = s['pac']
                
                if any(pac['r'] == g['r'] and pac['c'] == g['c'] for g in s['ghosts']):
                    s['over'] = True
                    s['won'] = True
                
                dots_left = sum(cell == 1 for row in s['grid'] for cell in row)
                if dots_left <= 0:
                    s['over'] = True
                    s['won'] = False
                
                if pac['steps'] > 0 and pac['steps'] % TRANSFER_STEPS == 0:
                    try_soul_transfer(s)
                    if not s['ghosts']:
                        s['over'] = True
                        s['won'] = True
                
                for corp in s['corpses'][:]:
                    corp['turns_left'] -= 1
                    if corp['turns_left'] <= 0:
                        if passable(corp['r'], corp['c']):
                            s['ghosts'].append({
                                'r':     corp['r'],
                                'c':     corp['c'],
                                'dr':    0,
                                'dc':    1,
                                'id':    corp['ghost_id'],
                                'color': corp['revive_color'],
                            })
                        s['corpses'].remove(corp)

        # ── Draw everything ──────────────────────────────────────────────
        screen.fill(BG)

        game_surf = pygame.Surface((W, H))
        game_surf.fill(BG)

        for r in range(ROWS):
            for c in range(COLS):
                if is_wall(r, c):
                    pygame.draw.rect(game_surf, WALL_COL, (c*CELL, r*CELL, CELL, CELL))
                    pygame.draw.rect(game_surf, WALL_INNER, (c*CELL+2, r*CELL+2, CELL-4, CELL-4), border_radius=3)
                elif s['grid'][r][c] == 1:
                    pygame.draw.circle(game_surf, DOT_COL,
                                     (c*CELL+CELL//2, r*CELL+CELL//2), 4)

        if s.get('blast_pos') and s.get('blast_timer', 0) > 0:
            draw_blast_effect(game_surf, s['blast_pos'][0], s['blast_pos'][1], s['blast_timer'])

        for corp in s['corpses']:
            draw_corpse(game_surf, corp['c']*CELL, corp['r']*CELL,
                       corp['turns_left'], corp['display_color'], fs)

        pac = s['pac']
        draw_pacman(game_surf, pac['c']*CELL, pac['r']*CELL,
                   pac['dr'], pac['dc'], s['mouth'], s.get('transfer_warning', False))

        for i, g in enumerate(s['ghosts']):
            draw_ghost(game_surf, g['c']*CELL, g['r']*CELL,
                      g['color'], i == s['selected'], str(g['id']+1), fs)

        draw_particles(game_surf, s)
        draw_hud(game_surf, fm, fs, s)

        screen.blit(game_surf, (shake_x, shake_y))

        if s.get('show_hint'):
            draw_controls_hint(screen, fh)

        if s['over']:
            if s['won']:
                draw_overlay(screen, fb, fm, "you caught him!", "press R to restart", s['score'])
            else:
                draw_overlay(screen, fb, fm, "pac-man wins!", "press R to restart", s['score'])

        pygame.display.flip()
        await asyncio.sleep(0)

    pygame.quit()


if __name__ == "__main__":
    asyncio.run(main())
