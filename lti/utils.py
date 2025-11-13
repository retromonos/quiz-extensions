# -*- coding: utf-8 -*-

import logging
import math
from logging.config import dictConfig

import requests
from canvasapi import Canvas
from canvasapi.exceptions import CanvasException

import config
from models import Quiz

dictConfig(config.LOGGING_CONFIG)
logger = logging.getLogger("app")

headers = {"Authorization": "Bearer " + config.API_KEY}
json_headers = {
    "Authorization": "Bearer " + config.API_KEY,
    "Content-type": "application/json",
}


def extend_quiz(quiz, is_new: bool, percent, user_id_list):
    """
    Extends a quiz time by a percentage for a list of users.

    :param quiz: A quiz object from Canvas
    :type quiz: dict
    :param is_new: Flag for if we are extending a either Classic or New Quiz.
    :type is_new: bool
    :param percent: The percent of original quiz time to be applied.
        e.g. 200 is double time, 100 is normal time, <100 is invalid.
    :type percent: int
    :param user_id_list: A list of Canvas user IDs to add time for.
    :type user_id_list: list
    :rtype: dict
    :returns: A dictionary with three parts:

        - success `bool` False if there was an error, True otherwise.
        - message `str` A long description of success or failure.
        - added_time `int` The amount of time added in minutes. Returns
        `None` if there was no time added.
    """
    # Debugging tag for new/classic quiz
    tag = "Classic"
    if is_new:
        tag = "New"

    quiz_id = quiz.id
    time_limit = quiz.__getattribute__("time_limit")

    if time_limit is None or time_limit < 1:
        msg = tag + " Quiz #{} has no time limit, so there is no time to add."
        return {"success": True, "message": msg.format(quiz_id), "added_time": None}

    added_time = int(
        math.ceil(time_limit * ((float(percent) - 100) / 100) if percent else 0)
    )

    quiz_extensions = []

    for user_id in user_id_list:
        user_extension = {"user_id": user_id, "extra_time": added_time}
        quiz_extensions.append(user_extension)

    try:
        # Change accomodation function based on if this is a new quiz
        if is_new:
            quiz.set_accomodations(quiz_extensions)
        else:
            quiz.set_extensions(quiz_extensions)
    except Exception as err:
        msg = (
            "Error creating extension for " + tag + " Quiz #{}. Canvas status code: {}"
        )
        return {
            "success": False,
            "message": msg.format(quiz_id, err),
            "added_time": None,
        }

    msg = "Successfully added {} minutes to " + tag + " Quiz #{}"
    return {
        "success": True,
        "message": msg.format(added_time, quiz_id),
        "added_time": added_time,
    }


# all occurances migrated except tests
def get_quizzes(course_id, per_page=config.MAX_PER_PAGE):
    """
    Get all quizzes in a Canvas course.

    :param course_id: The Canvas ID of a Course
    :type course_id: int
    :param per_page: The number of quizzes to get per page.
    :type per_page: int
    :rtype: list
    :returns: A list of dictionaries representing Canvas Quiz objects.
    """
    quizzes = []
    quizzes_url = "{}/api/v1/courses/{}/quizzes?per_page={}".format(
        config.API_URL, course_id, per_page
    )

    while True:
        quizzes_response = requests.get(quizzes_url, headers=headers)

        quizzes_list = quizzes_response.json()

        if "errors" in quizzes_list:
            break

        quizzes.extend(quizzes_list)

        try:
            quizzes_url = quizzes_response.links["next"]["url"]
        except KeyError:
            break

    return quizzes


# all occurances migrated except tests
def get_user(course_id, user_id):
    """
    Get a user from canvas by id, with respect to a course.

    :param user_id: ID of a Canvas course.
    :type user_id: int
    :param user_id: ID of a Canvas user.
    :type user_id: int
    :rtype: dict
    :returns: A dictionary representation of a User in Canvas.
    """
    response = requests.get(
        "{}/api/v1/courses/{}/users/{}".format(config.API_URL, course_id, user_id),
        params={"include[]": "enrollments"},
        headers=headers,
    )
    response.raise_for_status()

    return response.json()


# all occurances migrated except tests
def get_course(course_id):
    """
    Get a course from canvas by id.

    :param course_id: ID of a Canvas course.
    :type course_id: int
    :rtype: dict
    :returns: A dictionary representation of a Course in Canvas.
    """
    course_url = "{}/api/v1/courses/{}".format(config.API_URL, course_id)
    response = requests.get(course_url, headers=headers)
    response.raise_for_status()

    return response.json()


def get_or_create(session, model, **kwargs):
    """
    Simple version of Django's get_or_create for interacting with Models

    :param session: SQLAlchemy database session
    :type session: :class:`sqlalchemy.orm.scoping.scoped_session`
    :param model: The model to get or create from.
    :type model: :class:`flask_sqlalchemy.Model`
    """
    instance = session.query(model).filter_by(**kwargs).first()
    if instance:
        return instance, False
    else:
        instance = model(**kwargs)
        session.add(instance)
        session.commit()
        return instance, True


def missing_and_stale_quizzes(canvas: Canvas, course_id, quickcheck=False):
    """
    Find all quizzes that are in Canvas but not in the database (missing),
    or have an old time limit (stale)

    :param canvas: The Canvas API object.
    :type canvas: Canvas
    :param course_id: The Canvas ID of the Course.
    :type course_id: int
    :param quickcheck: Setting this to `True` will return when the
        first missing or stale quiz is found.
    :type quickcheck: bool
    :rtype: list
    :returns: A list of dictionaries representing missing quizzes. If
        quickcheck is true, only the first missing/stale result is returned.
    """
    course_obj = canvas.get_course(course_id)
    quizzes = list(course_obj.get_quizzes())

    # New Quizzes might not be implemented on a given installation
    try:
        new_quizzes = list(course_obj.get_new_quizzes())
    except CanvasException:
        logger.error(
            "Error fetching New Quizzes. Your Canvas installation may not support them."
        )
        new_quizzes = []

    all_quizzes = quizzes + new_quizzes

    num_quizzes = len(quizzes)

    missing_list = []

    for index, canvas_quiz in enumerate(all_quizzes):
        # Is true if the quiz is a New Quiz
        canvas_quiz.__setattr__("is_new", index >= num_quizzes)

        quiz = Quiz.query.filter_by(canvas_id=canvas_quiz.id).first()

        # quiz is missing or time limit has changed
        if not quiz or quiz.time_limit != canvas_quiz.__getattribute__("time_limit"):
            missing_list.append(canvas_quiz)

            if quickcheck:
                # Found one! Quickcheck complete.
                break

    return missing_list


def update_job(job, percent, status_msg, status, error=False):
    job.meta["percent"] = percent
    job.meta["status"] = status
    job.meta["status_msg"] = status_msg
    job.meta["error"] = error

    job.save()
