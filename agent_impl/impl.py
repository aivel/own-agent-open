from typing import List

from stats import stats_useage


def create_word_documents(assignment_id, deadline, teams_boards) -> List:
    results = []

    for i, team_board in enumerate(teams_boards):
        team_users_emails = [u['email'] for u in team_board.get_board_users()]

        doc_title = 'Assignment #{}, team: {}, deadline: {}'.format(assignment_id, team_board.get_name(), deadline)
        doc_st = stats_useage.create_file(doc_title, team_users_emails)
        doc_link = doc_st['link']

        results.append({
            'team_board': team_board,
            'team_board_name': team_board.get_name(),
            'team_name': team_board.get_name().split(' ')[-1].strip(),
            'doc_link': doc_link,
            'file_id': doc_st['file_id']
        })

    return results
