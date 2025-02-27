import os
from flask import Flask, request, abort, jsonify
from flask_sqlalchemy import SQLAlchemy
from flask_cors import CORS
import random

from models import setup_db, Question, Category

QUESTIONS_PER_PAGE = 10

def paginate_questions(request, selection):
    page = request.args.get("page", 1, type=int)
    start = (page - 1) * QUESTIONS_PER_PAGE
    end = start + QUESTIONS_PER_PAGE

    questions = [question.format() for question in selection]
    current_questions = questions[start:end]

    return current_questions

def create_app(test_config=None):
    # create and configure the app
    app = Flask(__name__)
    setup_db(app)

    CORS(app, resources={r"/": {"origins": "*"}})

    # CORS Headers
    @app.after_request
    def after_request(response):
        response.headers.add(
            "Access-Control-Allow-Headers", "Content-Type,Authorization,true"
        )
        response.headers.add(
            "Access-Control-Allow-Methods", "GET,PUT,POST,DELETE,OPTIONS"
        )
        return response

    """
    Handle GET requests
    for all available categories.
    """
    @app.route("/categories")
    def retrieve_categories():
        categories = {category.id: category.type
                      for category in Category.query.all()}

        return jsonify(
            {
                "success": True,
                "categories": categories,
                "total_categories": len(categories),
            }
        )

    """
    Handle GET requests for questions,
    including pagination (every 10 questions).
    This endpoint return a list of questions,
    number of total questions, current category, categories.
    """
    @app.route("/questions")
    def retrieve_questions():
        selection = Question.query.order_by(Question.id).all()
        current_questions = paginate_questions(request, selection)
        categories = {category.id: category.type
                      for category in Category.query.all()}

        if len(current_questions) == 0:
            abort(404)

        return jsonify(
            {
                "success": True,
                "questions": current_questions,
                "total_questions": len(Question.query.all()),
                "categories": categories,
                "current_category": 1
            }
        )

    """
    DELETE question using a question ID.
    """
    @app.route("/questions/<int:question_id>", methods=["DELETE"])
    def delete_question(question_id):
        try:
            question = Question.query.filter(Question.id == question_id).one_or_none()

            if question is None:
                abort(404)

            question.delete()
            selection = Question.query.order_by(Question.id).all()
            current_questions = paginate_questions(request, selection)

            return jsonify(
                {
                    "success": True,
                    "deleted": question_id,
                    "questions": current_questions,
                    "total_questions": len(Question.query.all()),
                }
            )

        except:
            abort(422)

    """
    Endpoint to POST a new question,
    which will require the question and answer text,
    category, and difficulty score.
    And to get questions based on a search term.
    It should return any questions for whom the search term
    is a substring of the question.
    """
    @app.route("/questions", methods=["POST"])
    def create_question():
        body = request.get_json()

        new_question = body.get("question", "")
        new_answer = body.get("answer", "")
        new_category = body.get("category", "")
        new_difficulty = body.get("difficulty", "")
        search = body.get("searchTerm", None)

        try:
            if search:
                selection = Question.query.order_by(Question.id).filter(
                    Question.question.ilike("%{}%".format(search))
                )
                current_questions = paginate_questions(request, selection)

                return jsonify(
                    {
                        "success": True,
                        "questions": current_questions,
                        "total_questions": len(selection.all()),
                    }
                )
            else:

                if (new_answer == "" or new_category == "" or
                    new_difficulty == "" or new_question == ""):
                    abort(422)

                question = Question(question=new_question, answer=new_answer, 
                                    category=new_category, difficulty=new_difficulty)
                question.insert()

                selection = Question.query.order_by(Question.id).all()
                current_questions = paginate_questions(request, selection)

                return jsonify(
                    {
                        "success": True,
                        "created": question.id,
                        "questions": current_questions,
                        "total_questions": len(Question.query.all()),
                    }
                )

        except:
            abort(422)

    """
    GET endpoint to get questions based on category.
    """
    @app.route("/categories/<int:categorie_id>/questions")
    def retrieve_questions_by_category(categorie_id):
        category = Category.query.filter(Category.id == categorie_id).one_or_none()
        if category is None:
            abort(404)
        else:
            selection = Question.query.order_by(Question.id).filter(
                Question.category == categorie_id
            )
            current_questions = paginate_questions(request, selection)

            return jsonify(
                {
                    "success": True,
                    "questions": current_questions,
                    "total_questions": len(selection.all()),
                }
            )

    """
    POST endpoint to get questions to play the quiz.
    This endpoint should take category and previous question parameters
    and return a random questions within the given category,
    if provided, and that is not one of the previous questions.
    """
    @app.route("/quizzes", methods=["POST"])
    def quizzes():
        body = request.get_json()

        previous_questions = body.get("previous_questions", [])
        quiz_category = body.get("quiz_category", None)
        
        try:
            available_questions = Question.query.order_by(Question.id).filter(
                ~Question.id.in_(previous_questions),
            ).all()

            questions = available_questions
            if quiz_category is not None and quiz_category["id"] != 0:
                questions = [question for question in available_questions 
                            if question.category == int(quiz_category["id"])]

            if len(questions) == 0:
                return jsonify(
                    {
                        "success": True,
                        "question": None
                    }
                )

            random_question = random.choice(questions)

            return jsonify(
                {
                    "success": True,
                    "question": random_question.format()
                }
            )

        except:
            abort(422)

    """
    Error handlers for all expected errors
    including 404 and 422.
    """

    @app.errorhandler(404)
    def not_found(error):
        return (
            jsonify({"success": False, "error": 404, "message": "resource not found"}),
            404,
        )

    @app.errorhandler(422)
    def unprocessable(error):
        return (
            jsonify({"success": False, "error": 422, "message": "unprocessable"}),
            422,
        )

    @app.errorhandler(400)
    def bad_request(error):
        return jsonify({"success": False, "error": 400, "message": "bad request"}), 400

    return app

