import json
import logging

import websocket

from agent_impl.impl import create_word_documents
from config import SETTINGS as S
from own_adapter.agent import Agent
from own_adapter.board import Board
from own_adapter.element import Element
from own_adapter.platform_access import PlatformAccess
from stats.stats_useage import create_teams_chart

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)


##


platform_access = PlatformAccess(S['own_space']['login'], S['own_space']['password'])
agent = Agent(platform_access)


SITE_URL_PREFIX = 'http://188.130.155.101:9002'
WORK_PROGRESS_CARD_TITLE = 'Work progress'
WORK_PROGRESS_CARD_TOP = 5
WORK_PROGRESS_CARD_WIDTH = 7
WORK_PROGRESS_CARD_HEIGHT = 5
TEAMS_PROGRESS_ROW_TOP = WORK_PROGRESS_CARD_TOP - 2
STUB_IMAGE_LINK = ' http://lorempixel.com/700/500/'
STUB_GOOGLE_DOC_LINK = 'https://somegoogledoclick.ru'
DB_FILENAME = 'teams_data.json'


def get_first_empty_cell(board, starting_from_row=0):
    cells = board.get_elements_matrix()

    for y, row in enumerate(cells):
        if y < starting_from_row:
            continue

        for x, elem in enumerate(row):
            if elem == 0:
                return x + 1, y + 1


def update_work_progress_chart(teacher_board, overall_stats_pic):
    # create chart image if not exists yet
    teacher_board_work_progress_elements = teacher_board.get_elements(WORK_PROGRESS_CARD_TITLE)

    if len(teacher_board_work_progress_elements) < 1:
        teacher_board.add_element(1, WORK_PROGRESS_CARD_TOP, WORK_PROGRESS_CARD_WIDTH,
                                  WORK_PROGRESS_CARD_HEIGHT, WORK_PROGRESS_CARD_TITLE)

    teacher_board_work_progress_elements = teacher_board.get_elements(WORK_PROGRESS_CARD_TITLE)

    if len(teacher_board_work_progress_elements) < 1:
        # could not create the chart
        return

    teacher_work_progress_card = teacher_board_work_progress_elements[0]

    teacher_work_progress_card.put_file('Work progress', open(overall_stats_pic, 'rb').read())

    # teacher_work_progress_card.put_link(STUB_IMAGE_LINK, STUB_IMAGE_LINK)


def post_assignment_for_team(assignment_id, assignment_download_link, doc_link, team_board):
    team_assignment_card_caption = 'HW #{}'.format(assignment_id)

    cell_x, cell_y = get_first_empty_cell(team_board)

    team_board.add_element(cell_x, cell_y, caption=team_assignment_card_caption)

    team_board_elements = team_board.get_elements(team_assignment_card_caption)

    if len(team_board_elements) < 1:
        return False

    created_elem = team_board_elements[0]

    # put a link to the assignment file
    created_elem.put_link(SITE_URL_PREFIX + assignment_download_link)

    # put a link to the google document
    created_elem.put_link(STUB_GOOGLE_DOC_LINK)  # doc_link

    return True


def update_team_card(teacher_board, team_board, team_stats_pic):
    team_name = team_board.get_name().split(':')[-1].strip()

    team_chart_elements = teacher_board.get_elements(team_name)

    if len(team_chart_elements) < 1:
        cell_x, cell_y = get_first_empty_cell(teacher_board, TEAMS_PROGRESS_ROW_TOP)

        teacher_board.add_element(cell_x, cell_y, caption=team_name)

        team_chart_elements = teacher_board.get_elements(team_name)

        if len(team_chart_elements) < 1:
            return False

    team_progress_chart_elem = team_chart_elements[0]

    team_progress_chart_elem.put_file(team_name, open(team_stats_pic, 'rb').read())
    # team_progress_chart_elem.put_link(STUB_IMAGE_LINK, STUB_IMAGE_LINK)

    return True


def save_teams_docs_links(docs_descriptors, work_name):
    teams = {}

    for doc_descriptor in docs_descriptors:
        teams[doc_descriptor['team_board_name']] = {
            'link': doc_descriptor['doc_link'],
            'file_id': doc_descriptor['file_id'],
            'work_name': work_name,
        }

    with open(DB_FILENAME, 'w', encoding='utf-8') as f:
        f.write(json.dumps(teams))

    return True


def on_ws_message(ws, message):
    global agent, platform_access

    message_dict = json.loads(message)
    content_type = message_dict['contentType']
    message_type = content_type.replace('application/vnd.uberblik.', '')

    logger.info(message)

    if message_type == 'liveUpdateElementCaptionEdited+json':
        # caption of a card has been updated
        element_caption = message_dict['newCaption']

        if element_caption.lower().startswith('hw'):
            element_id = message_dict['path']
            board_id = '/'.join(element_id.split('/')[:-2])
            teacher_board = Board.get_board_by_id(board_id, agent.get_platform_access(), need_name=False)

            assignment_element = Element.get_element_by_id(element_id, agent.get_platform_access(), teacher_board)

            if assignment_element is None:
                return

            assignment_files = assignment_element.get_files()

            if len(assignment_files) < 1:
                return

            assignment_file = assignment_files[-1]
            assignment_download_link = assignment_file.get_download_link()

            command_elements = [e.strip() for e in element_caption.split(',')]

            if len(command_elements) < 2:
                return

            assignment_id, deadline = command_elements[:2]
            assignment_id = int(assignment_id.split(' ')[1])

            # get teams' boards
            teams_boards = [b for b in agent.get_boards() if 'teacher' not in b.get_name().lower()]

            # create google documents
            docs_descriptors = create_word_documents(assignment_id=assignment_id, deadline=deadline,
                                                     teams_boards=teams_boards)

            save_teams_docs_links(docs_descriptors, 'HW #%s' % assignment_id)

            stats_pics = create_teams_chart([{
                'team_name': d['team_name'],
                'file_id': d['file_id']
            } for d in docs_descriptors], 'HW #%s' % assignment_id)

            for doc_descriptor in docs_descriptors:
                doc_link = doc_descriptor['doc_link']
                team_board = doc_descriptor['team_board']
                team_name = doc_descriptor['team_name']

                post_assignment_for_team(assignment_id, assignment_download_link, doc_link, team_board)

                team_stats_pic = [f for f in stats_pics['teams_pics'] if f['team_name'] == team_name]

                if len(team_stats_pic) < 1:
                    print('WARNING! NO PICTURE')
                    continue

                team_stats_pic = team_stats_pic[0]['stats_pic']

                update_team_card(teacher_board, team_board, team_stats_pic)

            update_work_progress_chart(teacher_board, stats_pics['overall_stats_pic'])


def on_websocket_error(ws, error):
    """Logs websocket errors"""
    logger.error(error)


def on_websocket_open(ws):
    """Logs websocket openings"""
    logger.info('Websocket is open')


def on_websocket_close(ws):
    """Logs websocket closings"""
    logger.info('Websocket is closed')


##


def run():
    global platform_access, agent

    platform_url_no_protocol = agent.get_platform_access().get_platform_url().split('://')[1]
    access_token = agent.get_platform_access().get_access_token()

    url = 'ws://{}/opensocket?token={}'.format(platform_url_no_protocol, access_token)

    ws = websocket.WebSocketApp(url,
                                on_message=on_ws_message,
                                on_error=on_websocket_error,
                                on_open=on_websocket_open,
                                on_close=on_websocket_close)
    ws.run_forever()
