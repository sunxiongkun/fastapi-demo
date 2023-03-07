import logging


# ===========================
# operators on coin keywords
# ===========================
def get_ai_picture(question: str = ''):
    try:
        return question
    except Exception as e:
        logging.exception("exception: {}", e)
