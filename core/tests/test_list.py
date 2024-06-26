"""Test LIST, filter, and pagination."""
import typing as typ
import unittest

import httpx
from faker import Faker
from fastapi import status
from fastapi.testclient import TestClient
from sqlmodel import Session

from app import engine
from core.tests.test_gadgets import (manual_create_task,
                                     prepare_users_for_test,
                                     remove_all_tasks_and_users)
from main import app

client = TestClient(app)


class TestList(unittest.TestCase):  # pylint: disable=too-many-public-methods
    """Test List, filter, and pagination."""

    def setUp(self) -> None:
        """Prepare the data for testing."""
        remove_all_tasks_and_users()
        prepare_users_for_test()

    def tearDown(self):
        """Remove all tasks and users."""
        remove_all_tasks_and_users()

    def before_test(self) -> typ.Tuple[int, int, int, int, int, int]:
        """Prepare the data for testing."""
        first_task_id = manual_create_task()
        second_task_id = manual_create_task()  # Update 2 times
        third_task_id = manual_create_task()  # Delete
        fourth_task_id = manual_create_task()  # Update 2 time and delete
        fifth_task_id = manual_create_task(has_user=False)

        # Expect 3 tasks in the ListView
        # Expect 1 + 3 + 1 + 3 + 1= 9 revisions(aka rows) in the TaskContent table.

        el_id = 2  # Legacy support
        return (
            el_id,
            first_task_id,
            second_task_id,
            third_task_id,
            fourth_task_id,
            fifth_task_id,
        )

    def _make_35_tasks(self) -> None:
        faker = Faker()
        faker.seed_instance(4321)

        with Session(engine) as session:
            for __ in range(35):
                _ = client.post(
                    '/create-task/',
                    json={
                        'title': faker.text()[:40],
                        'description': faker.text()[:40],
                        'status': faker.random_element(
                            elements=('pending', 'in_progress', 'completed')
                        ),
                        'due_date': faker.date(),
                        'created_by': faker.random_element(elements=(1, 2, 10)),
                    },
                )
            session.commit()

    def _test_user_created_sarit_updated(self) -> httpx.Response:
        (
            _,
            first_task_id,
            __,
            ___,
            ____,
            _____,
        ) = self.before_test()
        update_response = client.put(
            '/',
            json={
                'id': first_task_id,
                'title': 'Test update the title',
                'description': 'Test update description',
                'status': 'completed',
                'due_date': '2023-12-31',
                'created_by': 1,  # Default is 10. Let's update with 1 aka(sarit).
            },
        )
        return update_response

    def test_list_no_deleted_tasks(self) -> None:
        """List all tasks. Expect no deleted task."""
        (
            el_id,
            _,
            second_task_id,
            third_task_id,
            fourth_task_id,
            __,
        ) = self.before_test()
        second_task_response = client.put(
            '/',
            json={
                'id': second_task_id,
                'title': 'Intermediate title',
                'description': 'New desc',
                'status': 'pending',
                'due_date': '2022-12-31',
                'created_by': el_id,
            },
        )
        second_task_final_response = client.put(
            '/',
            json={
                'id': second_task_id,
                'title': 'Final title',
                'description': 'Final desc',
                'status': 'pending',
                'due_date': '2022-12-31',
                'created_by': el_id,
            },
        )

        deleted_response = client.delete(f"/{third_task_id}")

        # Last task in 2 updates and 1 delete
        fourth_task_updated_response = client.put(
            '/',
            json={
                'id': fourth_task_id,
                'title': 'Intermediate title',
                'description': 'New desc',
                'status': 'pending',
                'due_date': '2022-12-31',
                'created_by': el_id,
            },
        )
        fourth_task_last_updated_response = client.put(
            '/',
            json={
                'id': fourth_task_id,
                'title': 'Final title',
                'description': 'New desc',
                'status': 'pending',
                'due_date': '2022-12-31',
                'created_by': el_id,
            },
        )

        fourth_deleted_response = client.delete(f"/{fourth_task_id}")

        list_response = client.get('/')

        assert list_response.status_code == status.HTTP_200_OK
        assert 3 == list_response.json()['total']
        assert second_task_response.status_code == status.HTTP_200_OK
        assert second_task_final_response.status_code == status.HTTP_200_OK
        assert deleted_response.status_code == status.HTTP_204_NO_CONTENT
        assert fourth_task_updated_response.status_code == status.HTTP_200_OK
        assert fourth_task_last_updated_response.status_code == status.HTTP_200_OK
        assert fourth_deleted_response.status_code == status.HTTP_204_NO_CONTENT

    def test_filter_due_date_and_found(self) -> None:
        """Filter by exact due_date."""
        self.before_test()
        response = client.get('/?due_date=2022-12-31')
        assert response.status_code == status.HTTP_200_OK
        assert 5 == response.json()['total']

    def test_filter_due_date_and_not_found(self) -> None:
        """Filter by exact due_date."""
        self.before_test()
        response = client.get('/?due_date=2022-12-3')
        assert response.status_code == status.HTTP_200_OK
        assert 0 == response.json()['total']

    def test_filter_due_date_non_numeric_string(self) -> None:
        """Filter with non-numeric string."""
        response = client.get('/?due_date=some_string')
        assert response.status_code == status.HTTP_406_NOT_ACCEPTABLE
        assert response.json() == {
            'detail':
                [
                    {
                        'loc': ['due_date'],
                        'msg': "Invalid date format. Must be in 'YYYY-MM-DD' format.",
                        'type': 'ValueError'
                    }
                ]
        }

    def test_filter_status_and_found(self) -> None:
        """Filter by status."""
        self.before_test()
        response = client.get('/?task_status=pending')
        assert response.status_code == status.HTTP_200_OK
        assert response.json()['total'] == 5

    def test_filter_status_and_not_found(self) -> None:
        """Filter by status."""
        self.before_test()
        response = client.get('/?task_status=completed')
        assert response.status_code == status.HTTP_200_OK
        assert response.json()['total'] == 0

    def test_filter_due_date_and_status_and_found(self) -> None:
        """Filter by status."""
        self.before_test()
        response = client.get('/?due_date=2022-12-31&task_status=pending')
        assert response.status_code == status.HTTP_200_OK
        assert response.json()['total'] == 5

    def test_filter_due_date_and_status_and_not_found(self) -> None:
        """Filter by status."""
        self.before_test()
        response = client.get('/?due_date=2022-12-31&task_status=completed')
        assert response.status_code == status.HTTP_200_OK
        assert response.json()['total'] == 0

    def test_filter_created_by_username(self) -> None:
        """Found task based on given username."""
        self.before_test()
        response = client.get('/?created_by_username=test_user')
        assert response.status_code == status.HTTP_200_OK
        assert response.json()['total'] == 4

    def test_filter_created_by_username_not_found(self) -> None:
        """Not found task based on given username."""
        self.before_test()
        response = client.get('/?created_by_username=taksin')
        assert response.status_code == status.HTTP_406_NOT_ACCEPTABLE
        assert response.json() == {'detail': [{'loc': ['created_by_username'],
                                               'msg': 'User does not exist.',
                                               'type': 'ValueError'}]}

    def test_filter_due_date_and_status_and_username(self) -> None:
        """Filter by created_by."""
        self.before_test()
        response = client.get(
            '/?due_date=2022-12-31&task_status=pending&created_by_username=test_user'
        )
        assert response.status_code == status.HTTP_200_OK
        assert response.json()['total'] == 4

    def test_filter_due_date_and_status_and_wrong_username(self) -> None:
        """Filter by created_by."""
        # User does exist in database, but has no task.
        self.before_test()
        response = client.get(
            '/?due_date=2022-12-31&task_status=pending&created_by_username=elcolie'
        )
        assert response.status_code == status.HTTP_200_OK
        assert response.json() == {'items': [], 'total': 0, 'page': 1, 'size': 50, 'pages': 0}

    def test_filter_created_by_username_and_due_date(self) -> None:
        """Filter by created_by."""
        self.before_test()
        response = client.get('/?created_by_username=test_user&due_date=2022-12-31')
        assert response.status_code == status.HTTP_200_OK
        assert response.json()['total'] == 4

    def test_filter_created_by_wrong_username_and_valid_due_date(self) -> None:
        """Filter by created_by."""
        self.before_test()
        response = client.get('/?created_by_username=elcolie&due_date=2022-12-31')
        assert response.status_code == status.HTTP_200_OK
        assert response.json()['total'] == 0

    def test_filter_valid_created_by_and_valid_updated_by(self) -> None:
        """Filter by created_by, and updated_by username."""
        update_response = self._test_user_created_sarit_updated()
        response = client.get(
            '/?created_by_username=test_user&updated_by_username=sarit'
        )

        assert update_response.status_code == status.HTTP_200_OK
        assert update_response.json() == {'message': 'Instance updated successfully!'}

        assert response.status_code == status.HTTP_200_OK
        assert response.json() == {
            'items': [
                {
                    'id': 1,
                    'title': 'Test update the title',
                    'description': 'Test update description',
                    'due_date': '2023-12-31',
                    'status': 'StatusEnum.COMPLETED',
                    'created_by': 10,
                    'updated_by': 1,
                    'created_by_username': 'test_user',
                    'updated_by_username': 'sarit'
                }
            ],
            'total': 1,
            'page': 1,
            'size': 50,
            'pages': 1}

    def test_filter_created_by(self) -> None:
        """Filter by created_by username."""
        update_response = self._test_user_created_sarit_updated()
        response = client.get('/?created_by_username=test_user')
        assert update_response.status_code == status.HTTP_200_OK
        assert response.status_code == status.HTTP_200_OK
        assert response.json() == {
            'items': [
                {'id': 1,
                 'title': 'Test update the title',
                 'description': 'Test update description',
                 'due_date': '2023-12-31',
                 'status': 'StatusEnum.COMPLETED',
                 'created_by': 10,
                 'updated_by': 1,
                 'created_by_username': 'test_user',
                 'updated_by_username': 'sarit'},
                {'id': 2,
                 'title': 'Test Task with created_by',
                 'description': 'This is a test task',
                 'due_date': '2022-12-31',
                 'status': 'StatusEnum.PENDING',
                 'created_by': 10,
                 'updated_by': 10,
                 'created_by_username': 'test_user',
                 'updated_by_username': 'test_user'},
                {'id': 3,
                 'title': 'Test Task with created_by',
                 'description': 'This is a test task',
                 'due_date': '2022-12-31',
                 'status': 'StatusEnum.PENDING',
                 'created_by': 10,
                 'updated_by': 10,
                 'created_by_username': 'test_user',
                 'updated_by_username': 'test_user'},
                {'id': 4,
                 'title': 'Test Task with created_by',
                 'description': 'This is a test task',
                 'due_date': '2022-12-31',
                 'status': 'StatusEnum.PENDING',
                 'created_by': 10,
                 'updated_by': 10,
                 'created_by_username': 'test_user',
                 'updated_by_username': 'test_user'}
            ],
            'total': 4,
            'page': 1,
            'size': 50,
            'pages': 1}

    def test_filter_updated_by(self) -> None:
        """Filter by updated_by username."""
        update_response = self._test_user_created_sarit_updated()
        test_user_response = client.get('/?updated_by_username=test_user')
        sarit_response = client.get('/?updated_by_username=sarit')
        assert update_response.status_code == status.HTTP_200_OK
        assert test_user_response.json() == {
            'items': [
                {'id': 2,
                 'title': 'Test Task with created_by',
                 'description': 'This is a test task',
                 'due_date': '2022-12-31',
                 'status': 'StatusEnum.PENDING',
                 'created_by': 10,
                 'updated_by': 10,
                 'created_by_username': 'test_user',
                 'updated_by_username': 'test_user'},
                {'id': 3,
                 'title': 'Test Task with created_by',
                 'description': 'This is a test task',
                 'due_date': '2022-12-31',
                 'status': 'StatusEnum.PENDING',
                 'created_by': 10,
                 'updated_by': 10,
                 'created_by_username': 'test_user',
                 'updated_by_username': 'test_user'},
                {'id': 4,
                 'title': 'Test Task with created_by',
                 'description': 'This is a test task',
                 'due_date': '2022-12-31',
                 'status': 'StatusEnum.PENDING',
                 'created_by': 10,
                 'updated_by': 10,
                 'created_by_username': 'test_user',
                 'updated_by_username': 'test_user'}],
            'total': 3,
            'page': 1,
            'size': 50,
            'pages': 1}
        assert sarit_response.json() == {
            'items': [
                {'id': 1,
                 'title': 'Test update the title',
                 'description': 'Test update description',
                 'due_date': '2023-12-31',
                 'status': 'StatusEnum.COMPLETED',
                 'created_by': 10,
                 'updated_by': 1,
                 'created_by_username': 'test_user',
                 'updated_by_username': 'sarit'}
            ],
            'total': 1,
            'page': 1,
            'size': 50,
            'pages': 1}

    def test_filter_wrong_created_by_and_valid_updated_by(self) -> None:
        """Filter by created_by, and updated_by username."""
        update_response = self._test_user_created_sarit_updated()
        response = client.get('/?created_by_username=elcolie&updated_by_username=taksin')
        assert update_response.status_code == status.HTTP_200_OK
        assert response.status_code == status.HTTP_406_NOT_ACCEPTABLE
        assert response.json() == {'detail': [{'loc': ['updated_by_username'],
                                               'msg': 'User does not exist.',
                                               'type': 'ValueError'}]}

    def test_filter_invalid_created_by_and_valid_updated_by(self) -> None:
        """Filter by created_by, and updated_by username."""
        update_response = self._test_user_created_sarit_updated()
        response = client.get('/?created_by_username=maew&updated_by_username=taksin')
        assert update_response.status_code == status.HTTP_200_OK
        assert response.status_code == status.HTTP_406_NOT_ACCEPTABLE
        assert response.json() == {'detail': [{'loc': ['created_by_username'],
                                               'msg': 'User does not exist.',
                                               'type': 'ValueError'},
                                              {'loc': ['updated_by_username'],
                                               'msg': 'User does not exist.',
                                               'type': 'ValueError'}]}

    def test_pagination(self) -> None:
        """Test pagination."""
        self._make_35_tasks()
        first_page_size_by_five = client.get('/?page=1&size=5')
        second_page_size_by_five = client.get('/?page=2&size=5')
        first_page_size_by_seven = client.get('/?page=1&size=7')
        last_page_size_by_seven = client.get('/?page=5&size=7')

        first_page_size_by_five_id_list = [
            task['id'] for task in first_page_size_by_five.json()['items']
        ]
        first_page_size_by_five_id_list.sort()

        # Check 2nd page, size by 5
        second_page_id_list = [
            task['id'] for task in second_page_size_by_five.json()['items']
        ]
        second_page_id_list.sort()

        # Check 1st page, size by 7
        first_page_id_list = [
            task['id'] for task in first_page_size_by_seven.json()['items']
        ]
        first_page_id_list.sort()

        # Check 5th page(aka last page), size by 7
        last_page_id_list = [
            task['id'] for task in last_page_size_by_seven.json()['items']
        ]
        last_page_id_list.sort()

        assert [1, 2, 3, 4, 5] == first_page_size_by_five_id_list
        assert [6, 7, 8, 9, 10] == second_page_id_list
        assert [1, 2, 3, 4, 5, 6, 7] == first_page_id_list
        assert [29, 30, 31, 32, 33, 34, 35] == last_page_id_list

    def test_filter_and_pagination(self) -> None:
        """Filter + pagination."""
        self._make_35_tasks()
        post_response = client.post(
            '/create-task/',
            json={
                'title': 'Distinguish from the rest',
                'description': 'Tuna VS Sardine',
                'status': 'in_progress',
                'due_date': '3000-12-31',
                'created_by': 10,
            },
        )
        response = client.get('/?due_date=3000-12-31&_page_number=1&_per_page=5')
        assert post_response.status_code == status.HTTP_201_CREATED
        assert response.status_code == status.HTTP_200_OK
        assert response.json() == {
            'items': [
                {
                    'id': 36,
                    'title': 'Distinguish from the rest',
                    'description': 'Tuna VS Sardine',
                    'due_date': '3000-12-31',
                    'status': 'StatusEnum.IN_PROGRESS',
                    'created_by': 10,
                    'updated_by': 10,
                    'created_by_username': 'test_user',
                    'updated_by_username': 'test_user'
                }
            ],
            'total': 1,
            'page': 1,
            'size': 50,
            'pages': 1
        }


if __name__ == '__main__':
    unittest.main()
