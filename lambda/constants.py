import boto3
import os
from ask_sdk_model.er.dynamic import Entity, EntityValueAndSynonyms
from enum import Enum

ssm = boto3.client("ssm")

# ENUM DEFINITIONS
class QuestionType(Enum):
    GENERAL = "general"
    SPECIFIC = "specific"

class YearLevel(Enum):
    FIRST = "First Year"
    SECOND = "Second Year"
    THIRD = "Third Year"
    FOURTH = "Fourth Year"
    FIFTH = "Fifth Year"

class YesNo(Enum):
    YES = "yes"
    NO = "no"

class MessageType(Enum):
    SPEECH = "speech"
    REPROMPT = "reprompt"
    ASK_AGAIN = "ask again"
    FIRST_QUESTION = "first question"
    FIRST_SPECIFIC_QUESTION = "first specific question"
    CONFIRM_SPEC = "confirm spec"
    PROGRESSIVE_RESPONSE = "progressive response"
    GREETINGS = "greetings"

class Status(Enum):
    EMPTY = ""
    NO_MATCH = "no match"
    LOADED = "loaded"
    WAITING = "waiting"

# ARRTIBUTES & ENTITIES
BASE_URL = "http://" + ssm.get_parameter(Name = os.environ.get("URL_PARAM"))["Parameter"]["Value"]
ATTRIBUTES = ["question_type", "faculty", "program", "specialization", "year_level", "topic", "question", "answer", "ask_another_question"]

QUESTION_TYPE_ENTITIES = [
    Entity(name = EntityValueAndSynonyms(value = QuestionType.GENERAL, synonyms = ["general", "general question"])),
    Entity(name = EntityValueAndSynonyms(value = QuestionType.SPECIFIC, synonyms = ["specific", "specific question", "program specific question", "program specific"])),
]

YEAR_LEVEL_ENTITIES = [
    Entity(name = EntityValueAndSynonyms(value = YearLevel.FIRST, synonyms = ["First Year", "one", "1st year", "freshman", "first year"])),
    Entity(name = EntityValueAndSynonyms(value = YearLevel.SECOND, synonyms = ["Second Year", "two", "2nd year", "sophomore", "second year"])),
    Entity(name = EntityValueAndSynonyms(value = YearLevel.THIRD, synonyms = ["Third Year", "three", "3rd year", "junior", "third year"])),
    Entity(name = EntityValueAndSynonyms(value = YearLevel.FOURTH, synonyms = ["Fourth Year", "four", "4th year", "senior", "fourth year"])),
    Entity(name = EntityValueAndSynonyms(value = YearLevel.FIFTH, synonyms = ["Fifth Year", "five", "5th year", "graduate", "fifth year"])),
]

YES_NO_ENTITIES = [
    Entity(name = EntityValueAndSynonyms(value = YesNo.YES, synonyms = ["yes", "yeah", "yep", "I do", "yes please", "you know it"])),
    Entity(name = EntityValueAndSynonyms(value = YesNo.NO, synonyms = ["no", "nope", "no thank you", "I don't", "I do not"])),
]

# MESSAGES
LAUNCH_MESSAGES = {
    MessageType.SPEECH: "Welcome to Student Advising Assistant!! Do you want to ask a general question or program-specific question?",
    MessageType.REPROMPT: "Please tell me what type of question you want to ask."
}

QUESTION_TYPE_MESSAGES = {
    MessageType.FIRST_QUESTION: "OK. Now please tell me your faculty.",
    MessageType.FIRST_SPECIFIC_QUESTION: "OK. Please tell me your field of study.",
    MessageType.SPEECH: "OK. Please tell me the topic of your question.",
    MessageType.ASK_AGAIN: "Sorry, I didn't get that. Please tell me if you want to ask a general question or program-specific question."
}

FACULTY_MESSAGES = {
    MessageType.SPEECH: "What is your program?",
    MessageType.REPROMPT: "What is your program?",
    MessageType.ASK_AGAIN: "Sorry, I didn't get that. Please tell me your faculty again."
}

PROGRAM_MESSAGES = {
    MessageType.SPEECH: "What is the topic of your question?",
    MessageType.FIRST_SPECIFIC_QUESTION: "What is your field of study?",
    MessageType.ASK_AGAIN: "Sorry, I didn't get that. Please tell me your program again."
}

LOAD_SPEC_MESSAGES = {
    MessageType.SPEECH: "What is your year level?",
    MessageType.ASK_AGAIN: "Sorry, I could not find any specialization that matches your input. Please try again.",
    MessageType.CONFIRM_SPEC: "I have loaded the specialization options. Please tell me your specialization."
}

SPEC_MESSAGES = {
    MessageType.SPEECH: "Please tell me your year level.",
    MessageType.REPROMPT: "Please tell me your year level.",
    MessageType.ASK_AGAIN: "Sorry, I didn't get that. Please tell me your specialization again."
}

YEAR_MESSAGES = {
    MessageType.SPEECH: "Now please tell me the topic of your question.",
    MessageType.ASK_AGAIN: "Sorry, I didn't get that. Please tell me your year level again."
}

TOPIC_MESSAGES = {
    MessageType.SPEECH: "Please tell me your question."
}

CHECK_ANS_MESSAGES = {
    MessageType.ASK_AGAIN: "Sorry, I could not find any answer for your question.",
    MessageType.SPEECH: "<break time='3s' /> Do you want to ask another question?"
}

QUESTION_MESSAGES = {
    MessageType.PROGRESSIVE_RESPONSE: "Your question has been recorded. Please wait a moment while I generate the answer. <break time='10s' /> The answer is ready. Please ask 'Alexa, check answer.' to check the answer.",
    MessageType.SPEECH: "Your answer is ready. Please ask 'check answer.' to check your answer."
}

ASK_ANOTHER_Q_MESSAGES = {
    MessageType.GREETINGS: "Thank you for using the Student Advising Assistant. Goodbye!",
    MessageType.ASK_AGAIN: "Sorry, I didn't get that. Please answer either yes or no.",
    MessageType.SPEECH: "Great!! Please tell me if you want to ask a general question or a program specific question."
}