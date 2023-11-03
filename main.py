import copy
import pygame
import sys
import random
import time
import numpy
import json
from queue import PriorityQueue

INF = 9999999999

BLACK=(0,0,0)
WHITE=(255,255,255)

pygame.init()
pygame.display.set_caption("Tetris")

class Block:
    def __init__(self,name):
        self.name=name
        with open('block info/block-number map.json', 'r', encoding='utf-8') as file:
            block_number_map = json.load(file)
            self.num=block_number_map[name]

        #set matrix
        reader = Reader()
        block_info = reader.read_strings_from_txt(f'block matrixs/{name}.txt')
        matrix = reader.string_to_block(block_info)
        self.matrix = matrix
        self.size=len(self.matrix)

        #set rgb
        with open('block info//block rgbs.json', 'r', encoding='utf-8') as file:
            block_rgbs = json.load(file)
            self.rgb = block_rgbs[name]

        #set geometry
        self.pos=[0,5-self.size//2]
        self.rotation_cnt = 0

        #movement constants
        self.RIGHT=0
        self.UP=1
        self.LEFT=2
        self.DOWN=3

        self.dy=[0,-1,0,1]
        self.dx=[1,0,-1,0]
    def get_default(self):
        return Block(self.name)

    def get_shadow(self):
        block=copy.deepcopy(self)
        with open('block info/block rgbs.json', 'r', encoding='utf-8') as file:
            block_rgbs = json.load(file)
            block.rgb = block_rgbs["E"]
        return block
        
    def get_elements_in_board(self):
        elements=[]
        size=len(self.matrix)
        for i in range(size):
            for j in range(size):
                if self.matrix[i][j]:
                    elements.append([i+self.pos[0],j+self.pos[1]])
        return elements
        
    def move_by_dir(self, dir):
        self.pos=[self.pos[0]+self.dy[dir],self.pos[1]+self.dx[dir]]
    def get_moved_by_dir(self, dir):
        res = copy.deepcopy(self)
        res.move_by_dir(dir)
        return res
    def move(self,dis_vec):
        self.pos=[self.pos[i]+dis_vec[i] for i in range(2)]
    def get_moved(self, dis_vec):
        res = copy.deepcopy(self)
        res.move(dis_vec)
        return res

    def get_rotated_point(self, pos, center, deg):
        #x=j-center
        #y=i-center
        #res_x=-y
        #res_y=x
        #nj=res_x+center=center-y=2*center-i
        #ni=res_y+center=j
        #i,j -> j,2c-i -> 2c-i, 2c-j -> 2c-j, i
        y,x=pos[0],pos[1]
        if deg==90:
            return [2*center-x, y]
        elif deg==180:
            return [2*center-y,2*center-x]
        elif deg==270:
            return [x,2*center-y]
    def get_rotated(self, deg):
        size=len(self.matrix)
        if size==2: # O block
            return self
        center = (size-1)/2
        result_matrix=[[0]*size for i in range(size)]
        for i in range(size):
            for j in range(size):
                if self.matrix[i][j]:
                    y,x = self.get_rotated_point([i,j],center,deg)
                    y,x=int(y),int(x)
                    result_matrix[y][x]=self.matrix[i][j]
        result_block = copy.deepcopy(self)
        result_block.matrix = result_matrix
        result_block.rotation_cnt+=deg//90
        result_block.rotation_cnt%=4
        return result_block
    
    def get_rotated_clockwise(self):
        return self.get_rotated(2)
    def get_rotated_180(self):
        return self.get_rotated(1)
    def get_rotated_counterclockwise(self):
        return self.get_rotated(0)

class Reader:
    def __init__(self):
        return
    def read_strings_from_txt(self,txt_path):
        res_list = []
        with open(txt_path,'r') as f:
            flag=1
            while flag:
                line = f.readline()
                if flag==1:
                    flag=2
                else:
                    if not line: 
                        res_list.append(string)
                        break
                    res_list.append(string[:-1])
                string = line
                
        return res_list
    def string_to_block(self, lines):
        res_matrix = []
        for line in lines:
            row=[]
            for i in line:
                row.append(int(i))
            res_matrix.append(row)
        return res_matrix

class Resource:
    def __init__(self):
        reader = Reader()
        self.block_names=reader.read_strings_from_txt('block info/block names.txt')
        self.blocks = [Block(i) for i in self.block_names]
        with open('block info//block rgbs.json', 'r', encoding='utf-8') as file:
            self.block_rgbs = json.load(file)
        
        self.kick_data = reader.read_strings_from_txt('kick table/kick.txt')
        self.kick_data=list(map(eval,self.kick_data))
        
        self.kick_data_i = reader.read_strings_from_txt('kick table/kick_i.txt')
        self.kick_data_i=list(map(eval,self.kick_data_i))

        self.kick_data_180 = reader.read_strings_from_txt('kick table/kick_180.txt')
        self.kick_data_180=list(map(eval,self.kick_data_180))

        self.key_list = reader.read_strings_from_txt('event system/key list.txt')

class Graphic_Manager:
    def __init__(self, owner_instance, square_size=20, block_size=24,preview_block_size=28):
        self.owner_instance=owner_instance
        self.resource = Resource()
        self.screen = pygame.display.set_mode((0, 0), pygame.FULLSCREEN)
        self.SCREEN_WIDTH, self.SCREEN_HEIGHT = self.screen.get_size()

        self.square_size=square_size
        self.block_size=block_size
        self.preview_block_size = preview_block_size
        
        #
        vertical_center = self.SCREEN_HEIGHT/2
        horizontal_center = self.SCREEN_WIDTH/2
        self.board_start=[vertical_center - self.block_size*11, horizontal_center - self.block_size*5]
        self.board_end=[vertical_center + self.block_size*11, horizontal_center + self.block_size*5] 
        
    def draw_board_case(self):
        brick = Block('W')
        for i in range(-1,11):
            self.draw_block_piece_by_index(brick.rgb,-1,i)
            self.draw_block_piece_by_index(brick.rgb,22,i)
        for i in range(22):
            self.draw_block_piece_by_index(brick.rgb,i,-1)
            self.draw_block_piece_by_index(brick.rgb,i,10)

    def draw_block(self, block):
        color = block.rgb
        for i,j in block.get_elements_in_board():
            self.draw_block_piece_by_index(color, i, j)
    def draw_block_piece_by_pos(self, color, pos):
        y,x=pos[0],pos[1]
        def convert(x):
            return x-self.square_size/2+self.block_size/2
        assert convert(y)!=y
        y,x=convert(y),convert(x)
        
        pygame.draw.rect(self.screen, color, [x, y, self.square_size, self.square_size])
    def draw_block_piece_by_index(self, color, i, j):
        self.draw_block_piece_by_pos(color,[self.board_start[0]+self.block_size*i,self.board_start[1]+self.block_size*j])

    def draw_installed_blocks(self,board):
        for i in range(22):
            for j in range(10):
                block_name = self.resource.block_names[board[i][j]]
                self.draw_block_piece_by_index(self.resource.block_rgbs[block_name], i, j)
                
    def draw_board(self, board):
        self.screen.fill(BLACK)
        self.draw_board_case()
        self.draw_installed_blocks(board)
    
    def draw_block_queue(self, queue):
        block_queue = [Block(self.resource.block_names[i]) for i in queue]
        is_height_1 = False 
        for i in range(5):
            is_height_1 = block_queue[i].name=='I'
            if is_height_1:
                block_queue[i].pos[0] = 1+3*i+1.5-0.5
            else:
                block_queue[i].pos[0] = 1+3*i+1.5-1
            block_queue[i].pos[1]=13-block_queue[i].size/2
            self.draw_block(block_queue[i])

    def draw_hold(self, holding_block):
        holding_block.pos=[1,-holding_block.size/2-3.5]
        self.draw_block(holding_block)

    def draw_game_over(self):
        font = pygame.font.SysFont("notosanscjkkr",30)
        text = font.render(f"game over ",True,WHITE)
        r=text.get_rect()
        r.centerx=self.SCREEN_WIDTH/2
        r.centery=self.SCREEN_HEIGHT/2
        self.screen.blit(text,r) 
     
class Functions:
    def __init__(self):
        self.functions = {
            'linear':self.linear
        }
    def get_func(self, name, *args):
        return self.functions[name](*args)
    def linear(self, a, b):
        def axp_b(x):
            return a*x+b
        return axp_b
    
class Tetris:
    def __init__(self):
        #helper
        self.resource = Resource()
        self.graphic_manager = Graphic_Manager(self)
        self.func_helper = Functions()

        #event queue
        self.event_queue_counter=0
        self.event_queue={}
        self.events_in_loop={}

        #board and block
        self.curr_block = None
        self.holding_block = None
        self.dropped = None
        self.block_queue=[]
        self.board=[[0 for j in range(10)] for i in range(22)]
        self.used_hold = False

        #rotation
        self.rotation_counter=0

        #movement
        self.RIGHT=0
        self.UP=1
        self.LEFT=2
        self.DOWN=3

        self.dy=[0,-1,0,1]
        self.dx=[1,0,-1,0]

        #gravity
        self.gravity_period = 1
        self.lock_delay_func = self.func_helper.get_func('linear', -1/5, 1)
        self.lock_delay_count = 0
        self.lock_delay = 0
        self.whether_reaches_ground = False
        self.whether_reaches_ground_prev = False
        self.gravity_action_event_key = None

        #time
        self.started_time=time.time()
        self.finished_time=0

        #sound
        self.sounds ={}
        for i in ['blaster', 'reloading', 'shotgun-firing', 'sniper-firing']:
            self.sounds[i] = pygame.mixer.Sound(f'sounds/{i}.mp3')
        
        ###
        #key binding

        self.key_input_recorder={}
        for i in self.resource.key_list:
            self.key_input_recorder[i] = {
                'up':False,
                'down':False,
                'hold':0
            }

        #event
        self.event_map_default={}
        with open('event system/event map.json', 'r', encoding='utf-8') as file:
            self.event_map_default = json.load(file)
        self.event_map = copy.deepcopy(self.event_map_default)
        self.event_map_on_ground = copy.deepcopy(self.event_map_default)

        self.pull_down_input = None
        for key in self.event_map_on_ground.keys():
            if self.event_map_on_ground[key] == 'try_pull_down_block':
                self.pull_down_input=key
                break
        del self.event_map_on_ground[self.pull_down_input]

        self.event_delete_reservation_onehot = {}
        self.event_addition_reservation_list = []
        self.game_over_flag=False
        self.exit_flag=False
        self.event_queue_clear_reservation_flag=False
        self.event_map_change_reservation=None

        #function map
        self.func_map = {
            'try_move_block_to_left' : self.try_move_block_to_left,
            'try_move_block_to_right' : self.try_move_block_to_right,
            'try_pull_down_block' : self.try_pull_down_block,
            'drop_block' : self.drop_block,
            'rotate_block_clockwise' : self.rotate_block_clockwise,
            'rotate_block_counterclockwise' : self.rotate_block_counterclockwise,
            'rotate_block_180' : self.rotate_block_180,
            'cheat' : self.cheat,
            'act_gravity' : self.act_gravity,
            'None': lambda : None,
            "hold_curr_block" : self.hold_curr_block,
            'exit_game' : self.exit_game
        }

        #start
        self.start()

    def start(self):
        self.add_blocks_to_queue()
        self.grab_block()
        self.add_gravity_event()
    def exit_game(self):
        self.exit_flag = True
    def hold_curr_block(self):
        if self.used_hold:
            return
        
        #t: swapping route variable
        t=self.holding_block
        self.holding_block=self.curr_block.get_default()
        if t is None:
            self.grab_block()
        else:
            self.curr_block=t.get_default()
            self.update_lock()
        self.used_hold = True

    def display(self):
        self.graphic_manager.draw_board(self.board)
        
        if self.dropped is not None:
            self.graphic_manager.draw_block(self.dropped)
        
        if self.holding_block is not None:
            self.graphic_manager.draw_hold(self.holding_block)
        self.graphic_manager.draw_block_queue(self.block_queue)
        
        self.graphic_manager.draw_block(self.curr_block)
        

        if self.game_over_flag:
            self.graphic_manager.draw_game_over()
        
        
        pygame.display.update()
    
    def reaches_ground(self):
        return self.overlaps(self.curr_block.get_moved_by_dir(self.DOWN))
    def reserve_delete_event(self, key):
        self.event_delete_reservation_onehot[key]=1

    def event_process(self):
        t=time.time()
        for key in self.event_queue.keys():
            if self.event_queue_clear_reservation_flag:
                break
            if self.event_delete_reservation_onehot[key]:
                continue
            executation_time = self.event_queue[key][1]
            cmd=self.event_queue[key][0]

            if executation_time<=t:
                if type(cmd)==list:
                    for j in cmd:
                        self.execute_cmd(j)
                        self.reserve_delete_event(i)
                else:
                    self.execute_cmd(cmd)
                    self.reserve_delete_event(key)
        if self.event_queue_clear_reservation_flag:
            self.event_queue = {}
            self.event_addition_reservation_list = []
            self.event_delete_reservation_onehot = {}
            self.event_queue_clear_reservation_flag=False
        
        for key, value in self.event_addition_reservation_list:
            self.event_queue[key] = value
            if not key in self.event_delete_reservation_onehot:
                self.event_delete_reservation_onehot[key]=0

        delete_event_list = []
        for key in self.event_delete_reservation_onehot.keys():
            if self.event_delete_reservation_onehot[key]:
                del self.event_queue[key]
                delete_event_list.append(key)

        for key in delete_event_list:
            del self.event_delete_reservation_onehot[key]

        self.event_addition_reservation_list=[]

    def loop(self):
        self.display()
        self.deal_input()
        self.event_process()

    def cheat(self):
        for i in range(22):
            for j in range(10):
                self.board[i][j]=0

    #movement

    def can_move_block(self, dir):       
        cand = self.curr_block.get_moved_by_dir(dir)
        return not self.overlaps(cand)
    def try_move_block(self, dir):
        if self.can_move_block(dir):
            self.curr_block.move_by_dir(dir)
            self.update_lock()
            return True
        return False
            #play
    def try_move_block_to_left(self):
        self.try_move_block(self.LEFT)
    def try_move_block_to_right(self):
        self.try_move_block(self.RIGHT)
    def try_pull_down_block(self):
        assert not self.overlaps(self.curr_block)
        if self.try_move_block(self.DOWN):
            self.reserve_delete_event(self.gravity_action_event_key)
            self.add_gravity_event()
            
    #gravity
    def reset_gravity(self):
        self.reserve_delete_event(self.gravity_action_event_key)
        self.add_gravity_event()
    def add_gravity_event(self):
        self.reserve_add_event('act_gravity', self.gravity_period)
        self.gravity_action_event_key = self.event_queue_counter
        print(self.gravity_action_event_key)
    
    def act_gravity(self):
        if self.whether_reaches_ground:
            self.install_block()
            self.grab_block()
            if self.game_over_flag:
                return
            self.update_lock()
            self.add_gravity_event()
            return
        self.curr_block.move_by_dir(self.DOWN)
        self.update_lock()
        self.add_gravity_event()

    def update_lock(self):
        self.update_arrival_info()

        if self.whether_reaches_ground and self.whether_reaches_ground_prev:
            self.update_lock_delay()
        elif self.whether_reaches_ground and not self.whether_reaches_ground_prev:
            self.event_map_change_reservation='on_ground'
        elif not self.whether_reaches_ground and self.whether_reaches_ground_prev:
            self.event_map_change_reservation='default'
        self.set_dropped()
    def update_lock_delay(self):    
        if self.lock_delay_count < 5:
            self.reset_gravity()
            self.lock_delay_count+=1
    def update_arrival_info(self):
        self.whether_reaches_ground_prev = self.whether_reaches_ground
        self.whether_reaches_ground = self.reaches_ground()
        
    def set_dropped(self):
        self.dropped = self.curr_block.get_shadow()
        while not self.overlaps(self.dropped):
            self.dropped.move_by_dir(self.DOWN)
        self.dropped.move_by_dir(self.UP)

    def drop_block(self):
        self.curr_block.pos=self.dropped.pos
        self.install_block()
        self.grab_block()
        if self.game_over_flag:
            return
        self.update_lock()
        self.reset_gravity()
    
    #block interaction
    def is_full_line(self, i):
        for j in range(10):
            if self.board[i][j]==0:
                return False
        return True
    def clear_full_lines(self, added_lines):
        full_lines = []
        for i in added_lines:
            if self.is_full_line(i):
                full_lines.append(i)
        if full_lines == []:
            return
        for i in full_lines:
            for j in range(10):
                self.board[i][j]=0
        #sort by descending order
        full_lines=sorted(full_lines)
        full_lines.reverse()
        self.pull_down_lines(full_lines)
    def move_line(self, start, dest):
        for j in range(10):
            self.board[dest][j]=self.board[start][j]
    def pull_down_lines(self, cleared_lines):
        for i in range(len(cleared_lines)):
            start=cleared_lines[i]+i
            end=0
            if i+1==len(cleared_lines):
                end=i
            else:
                end=cleared_lines[i+1]+i
            for j in range(start, end, -1):
                start_line=j-(i+1)
                self.move_line(start_line,j)

    def install_block(self):
        added_lines = set()
        for i,j in self.curr_block.get_elements_in_board():
            self.board[i][j] = self.curr_block.num
            added_lines.add(i)
        self.clear_full_lines(added_lines)
        #play
        
    def grab_block(self):
        self.curr_block = Block(self.resource.block_names[self.block_queue[0]])
        del self.block_queue[0]
        if len(self.block_queue)<5:
            self.add_blocks_to_queue()
        self.used_hold = False
        self.lock_delay_count = 0
        if self.overlaps(self.curr_block):
            self.game_over()
            return     

    def is_valid_pos(self, y,x):
        y_valid = 0<=y and y<22
        x_valid = 0<=x and x<10
        return y_valid and x_valid
    def overlaps(self, block):
        elements = block.get_elements_in_board()
        for y,x in elements:
            if not self.is_valid_pos(y,x):
                return True
            if self.board[y][x]:
                return True
        return False
    ###
    def get_kick_table(self, deg):
        kick_table=[]
        if deg==180:
            kick_table=self.resource.kick_data_180[self.curr_block.rotation_cnt]                
        else:
            table=[]
            if self.curr_block.name == 'I':
                if deg==270:
                    table = self.resource.kick_data_i[4:]
                else:
                    table = self.resource.kick_data_i[:4]
            else:
                if deg==270:
                    table = self.resource.kick_data[4:]
                else:
                    table = self.resource.kick_data[:4]
            kick_table = table[self.curr_block.rotation_cnt]
        return kick_table
    def add_blocks_to_queue(self):
        self.block_queue += list(numpy.random.permutation(list(range(1,8))))

    #rotation
    def rotate_curr_block(self, deg):
        #play
        rotated_block = self.curr_block.get_rotated(deg)
        kick_table = self.get_kick_table(deg)
        kick_table=[(0,0)]+list(kick_table)
        for movement in kick_table:
            curr_cand = rotated_block.get_moved(movement)
            if not self.overlaps(curr_cand):
                self.curr_block = curr_cand
                self.update_lock()
                return
    def rotate_block_clockwise(self):
        self.rotate_curr_block(270)
    def rotate_block_counterclockwise(self):
        self.rotate_curr_block(90)
    def rotate_block_180(self):
        self.rotate_curr_block(180)

    def min(a, b):
        if a<=b:
            return a
        return b
    
    ###
    def game_over(self): 
        self.event_queue_clear_reservation_flag=True
        self.dropped=None
        self.finished_time = time.time()
        self.game_over_flag = True
        self.event_map = {'down, escape':'exit_game'}
    
    #event
    def reserve_add_event(self, cmd, delay):
        self.event_queue_counter+=1
        event = [self.event_queue_counter, [cmd, time.time()+delay]]
        self.event_addition_reservation_list.append(event)
        self.event_delete_reservation_onehot[self.event_queue_counter] = 0
    def execute_cmd(self,cmd):
        if type(cmd)==list and len(cmd)==2:
            delay = cmd[1]
            event = cmd[0]
            self.reserve_add_event(event, delay)
        else:
            self.func_map[cmd]()

    #input
    def is_input_occured(self,commands):
        event_type = commands[0]
        key=commands[1]
        
        if event_type=='hold':
        
            holding_start_time = self.key_input_recorder[key]['hold']
            if holding_start_time==0:
                return False
            
            func_name = commands[2]
            func=None
            if len(commands)>3:
                func = self.func_helper.get_func(func_name, *map(float, commands[3:-1]))
        
            dt=time.time()-holding_start_time
            cnt=float(commands[-1])
            return func(dt)>=cnt+1
        
        elif event_type=='down' or event_type=='down hold':
            return self.key_input_recorder[key]['down']
        
        elif event_type=='up':
            return self.key_input_recorder[key]['up']
    ##########
        # !!! event interpretation rule !!!
        # input interpretation
        # down, {key} = check if {key} is pressed in this frame 
        # up, {key} = check if {key} is unpressed in this frame 
        # hold, {func}, {args}, {cnt} = check if {func}({args}) ({holding time}) >=cnt+1
        # down hold, {func}, {args}, {cnt} = check if {key} is pressed in this frame or {func}({args}) ({holding time}) >=cnt+1
        
        # {func} = excute {func} 
        # {func}, {delay} = excute {func} {delay} later 
    ##########

    def deal_input(self):
        addition_reservation_list = []
        delete_reservation_list = []
        if self.event_map_change_reservation is not None:
            if self.event_map_change_reservation=='default':
                self.event_map = self.event_map_default
            elif self.event_map_change_reservation=='on_ground':
                self.event_map = self.event_map_on_ground
            self.event_map_change_reservation=None
    
        for cmd_str in self.event_map.keys():
            cmd = cmd_str.split(', ')
            if self.is_input_occured(cmd):
                self.execute_cmd(self.event_map[cmd_str])
                if cmd[0]=='down hold':
                    cmd[0]='hold'
                    cmd.append('0')
                    new_cmd_str = ', '.join(cmd)
                    addition_reservation_list.append([new_cmd_str, self.event_map[cmd_str]])
                elif cmd[0]=='hold':
                    cnt=int(cmd[-1])
                    cmd[-1]=str(cnt+1)
                    new_cmd_str = ', '.join(cmd)
                    addition_reservation_list.append([new_cmd_str,self.event_map[cmd_str]])
                    # delete_reservation_list.append(cmd_str)
        
        for key,value in addition_reservation_list:
            self.event_map[key]=value
        for key in delete_reservation_list:
            del self.event_map[key]
        for i in self.key_input_recorder.keys():
            self.key_input_recorder[i]['up']=False
            self.key_input_recorder[i]['down']=False


    def deal_keydown(self, event_key):
        self.key_input_recorder[event_key]['hold']=time.time()
        self.key_input_recorder[event_key]['down']=True
        
    def deal_keyup(self, event_key):
        self.key_input_recorder[event_key]['hold']=0
        self.key_input_recorder[event_key]['up']=True

        hold_event_key = f"hold {event_key}"
        if hold_event_key in self.event_map:
            del self.event_map[hold_event_key]

class Play_Tetris:
    def __init__(self):
        self.tetris=Tetris()
        self.QUIT = -1
        self.OK = 1
        self.GAME_OVER = 0
        self.clock = pygame.time.Clock()

    def run(self, fps):
        status=self.OK
        while True:
            if status == self.QUIT:
                break
            self.clock.tick(fps)
            status = self.update()
            if status == self.OK:
                self.tetris.display()
            elif status == self.GAME_OVER:
                pass
    def update(self):
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                return self.QUIT
            elif event.type == pygame.KEYDOWN:
                keyname = pygame.key.name(event.key)
                self.tetris.deal_keydown(keyname)
            elif event.type == pygame.KEYUP:
                keyname = pygame.key.name(event.key)
                self.tetris.deal_keyup(keyname)
        self.tetris.loop()
        if self.tetris.exit_flag:
            return self.QUIT
        if self.tetris.game_over_flag:
            return self.GAME_OVER
        else:
            return self.OK

game = Play_Tetris()
game.run(60)