import json
import random
import time

from own_adapter.agent import Agent
from own_adapter.platform_access import PlatformAccess
from config import SETTINGS as S
from stats.stats_useage import check_need_push, create_teams_chart

platform_access = PlatformAccess(S['own_space']['login'], S['own_space']['password'])
agent = Agent(platform_access)


DB_FILENAME = 'teams_data.json'
WORK_PROGRESS_CARD_TITLE = 'Work progress'


def get_boards():
    team_boards = []
    teacher_board = None

    for b in agent.get_boards():
        if 'teacher' not in b.get_name().lower():
            team_boards.append(b)
        else:
            teacher_board = b

    return teacher_board, team_boards


def update_work_progress_charts():
    with open(DB_FILENAME, 'r', encoding='utf-8') as f:
        teams_data = f.read()

    teams_data = json.loads(teams_data)

    teams = []
    work_name = None

    for key, val in teams_data.items():
        teams.append({
            'team_name': key.split(' ')[-1].strip(),
            'file_id': val['file_id'],
        })
        work_name = val['work_name']

    charts = create_teams_chart(teams, work_name)

    overall_stats_pic = charts['overall_stats_pic']
    teams_stats_pics = charts['teams_pics']

    teacher_board, team_boards = get_boards()

    work_card = teacher_board.get_elements(WORK_PROGRESS_CARD_TITLE)

    if len(work_card) < 1:
        return

    work_card = work_card[0]

    work_card.put_file(WORK_PROGRESS_CARD_TITLE, open(overall_stats_pic, 'rb').read())

    for team_board in team_boards:
        team_name = team_board.get_name().split(' ')[-1]
        team_stats_pic = [f for f in teams_stats_pics if f['team_name'] == team_name]

        if len(team_stats_pic) < 1:
            print('WARNING! NO PICTURE')
            continue

        team_stats_pic = team_stats_pic[0]['stats_pic']

        team_elements = teacher_board.get_elements(team_name)

        if len(team_elements) < 1:
            continue

        team_elem = team_elements[0]

        team_elem.put_file(team_name, open(team_stats_pic, 'rb').read())

    # overall chart
    # charts of particular teams


def send_notifications():
    with open(DB_FILENAME, 'r', encoding='utf-8') as f:
        teams_data = f.read()

    teams_data = json.loads(teams_data)

    team_boards = [b for b in agent.get_boards() if 'teacher' not in b.get_name().lower()]

    RANDOM_QUOTES = ["Hi guys! As I can see, you have not been doing anything for the past 3 days. Maybe you need "
                     "some help?", "How are you guys doing?", "Hey guys, it seems like you have not been doing anything",
                     "Hello guys! Deadline is coming, hurry up!", "Hello guys. If you do not want troubles, please, "
                                                                  "report your progress",
                     "Just wondering.. May be you need some help?", "Can I help you with the task?",
                     "Is there any relevant reason for you guys doing nothing for the past 3 days?"]

    for board in team_boards:
        team_board_name = board.get_name()

        file_id = teams_data[team_board_name]['file_id']

        if check_need_push(file_id):
            # need to push
            board.put_message(random.choice(RANDOM_QUOTES))


def run():
    global agent, platform_access

    while True:
        update_work_progress_charts()

        time.sleep(5)

        send_notifications()

        time.sleep(15)

