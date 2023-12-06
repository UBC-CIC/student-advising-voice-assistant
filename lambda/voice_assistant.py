from ask_sdk_core.dispatch_components import AbstractRequestHandler
from ask_sdk_core.api_client import DefaultApiClient
from ask_sdk_core.utils import is_request_type, is_intent_name
from ask_sdk_core.skill_builder import CustomSkillBuilder
from ask_sdk_model.services.directive import (
    SendDirectiveRequest, Header, SpeakDirective)
from ask_sdk_model.dialog import DynamicEntitiesDirective
from ask_sdk_model.er.dynamic import UpdateBehavior, EntityListItem, Entity, EntityValueAndSynonyms
from ask_sdk_model.slu.entityresolution.status_code import StatusCode

from constants import *

import requests
import re

# Constants
BASE_URL = "http://student-advising-voice-assitant-demo.ca-central-1.elasticbeanstalk.com/"

# SkillBuilder initialization
sb = CustomSkillBuilder(api_client=DefaultApiClient())

'''
Helper functions
    - get_canonical_value(handler_input, slot_name): given synonyms, returns the canonical value (original value assigned to the slot)
    - replace_dynamic_entities(handler_input, entities, slot_name): replaces the dynamic entities in the Alexa skill with the given entities
    - clear_dynamic_entities(handler_input, slot_name): clears the dynamic entities in the Alexa skill for the given slot
    - set_attribute(handler_input, key, val): sets the given attribute (key) to the given value (val)
    - get_attribute(handler_input, key): gets the given attribute (key)
    - is_first_question(handler_input): returns true if the current question is the first question
    - is_first_specific_question(handler_input): returns true if the current question is the first program-specific question
    - add_faculty_entities(handler_input): adds the faculty entities to the Alexa skill (called when user chooses the question type)
    - is_specific: returns true if the question type is specific
    - is_attribute_empty: returns true if the given attribute is empty
'''
def get_canonical_value(handler_input, slot_name):
        input = handler_input.request_envelope.request.intent.slots[slot_name].resolutions.resolutions_per_authority[1]
        print(input.status.code)
        return Status.NO_MATCH if input.status.code == StatusCode.ER_SUCCESS_NO_MATCH else input.values[0].value.name

def replace_dynamic_entities(handler_input, entities, slot_name):

    replace_entity_directive = DynamicEntitiesDirective(
            update_behavior = UpdateBehavior.REPLACE,
            types = [EntityListItem(name = slot_name, values = entities)]
        )
    
    handler_input.response_builder.add_directive(replace_entity_directive)

def clear_dynamic_entities(handler_input, slot_name):

    clear_entity_directive = DynamicEntitiesDirective(
            update_behavior = UpdateBehavior.CLEAR,
            types = [EntityListItem(name = slot_name)]
        )
    
    handler_input.response_builder.add_directive(clear_entity_directive)

def set_attribute(handler_input, key, val):
    handler_input.attributes_manager.session_attributes[key] = val

def get_attribute(handler_input, key):
    return handler_input.attributes_manager.session_attributes[key]

def is_first_question(handler_input):
    return get_attribute(handler_input, "faculty") == Status.EMPTY and get_attribute(handler_input, "program") == Status.EMPTY
    
def is_first_specific_question(handler_input):
    return get_attribute(handler_input, "question_type") == QuestionType.SPECIFIC and get_attribute(handler_input, "specialization") == Status.EMPTY and get_attribute(handler_input, "year_level") == Status.EMPTY

def add_faculty_entities(handler_input):
    faculties = requests.get(BASE_URL + "faculties").json()
    print(faculties)
    new_entities = []
    for faculty in faculties:
        entity_value = EntityValueAndSynonyms(value = faculty, synonyms = [faculty.lower(), faculty.lower().replace('the ', '')])
        entity = Entity(name = entity_value)
        new_entities.append(entity)
    replace_dynamic_entities(handler_input, new_entities, "CATCHALL")

    return QUESTION_TYPE_MESSAGES[MessageType.FIRST_QUESTION]

def is_specific(handler_input):
    return get_attribute(handler_input, "question_type") == QuestionType.SPECIFIC

def is_attribute_empty(handler_input, attribute):
    return get_attribute(handler_input, attribute) == Status.EMPTY

# Request Handlers
class LaunchRequestHandler(AbstractRequestHandler):

    def can_handle(self, handler_input):
        return is_request_type("LaunchRequest")(handler_input)
    
    def handle(self, handler_input):

        self.initialize_session_attributes(handler_input)

        replace_dynamic_entities(handler_input, QUESTION_TYPE_ENTITIES, "CATCHALL")
        
        return (
            handler_input.response_builder
            .speak(LAUNCH_MESSAGES[MessageType.SPEECH])
            .ask(LAUNCH_MESSAGES[MessageType.REPROMPT]).set_should_end_session(False).response
        )
    
    def initialize_session_attributes(self, handler_input):
        for attribute in ATTRIBUTES:
            set_attribute(handler_input, attribute, Status.EMPTY)

class CatchAllIntentHandler(AbstractRequestHandler):
    def can_handle(self, handler_input):
        return is_intent_name("CatchAllIntent")(handler_input)
    
    def handle(self, handler_input):
        if is_attribute_empty(handler_input, "question_type"):
            return self.handle_question_type(handler_input)
        elif is_attribute_empty(handler_input, "faculty"):
            return self.handle_faculty(handler_input)
        elif is_attribute_empty(handler_input, "program"):
            return self.handle_program(handler_input)
        elif is_specific(handler_input) and is_attribute_empty(handler_input, "specialization"):
            return self.load_specialization(handler_input) 
        elif get_attribute(handler_input, "specialization") == Status.LOADED:
            return self.handle_specialization(handler_input)
        elif is_specific(handler_input) and is_attribute_empty(handler_input, "year_level"):
            return self.handle_year_level(handler_input)
        elif is_attribute_empty(handler_input, "topic"):
            return self.handle_topic(handler_input)
        elif get_attribute(handler_input, "ask_another_question") == Status.WAITING:
            return self.handle_ask_another_question(handler_input)
        elif not is_attribute_empty(handler_input, "question"):
            return self.handle_check_answer(handler_input)
        else:
            return self.handle_question(handler_input)
    
    def handle_question_type(self, handler_input):
        rb = handler_input.response_builder
        question_type = get_canonical_value(handler_input, "text")

        if question_type == Status.NO_MATCH:
            speech_text = QUESTION_TYPE_MESSAGES[MessageType.ASK_AGAIN]
            return rb.speak(speech_text).ask(speech_text).response

        set_attribute(handler_input, "question_type", question_type)
        clear_dynamic_entities(handler_input, "CATCHALL")

        if is_first_question(handler_input):
            speech_text = add_faculty_entities(handler_input)
        elif is_first_specific_question(handler_input):
            speech_text = QUESTION_TYPE_MESSAGES[MessageType.FIRST_SPECIFIC_QUESTION]
        else:
            speech_text = QUESTION_TYPE_MESSAGES[MessageType.SPEECH]

        return rb.speak(speech_text).ask(speech_text).response
    
    def handle_faculty(self, handler_input):
        rb = handler_input.response_builder
        faculty_name = get_canonical_value(handler_input, "text")

        if faculty_name == Status.NO_MATCH:
            speech_text = FACULTY_MESSAGES[MessageType.ASK_AGAIN]
            return rb.speak(speech_text).ask(speech_text).response
        
        set_attribute(handler_input, "faculty", faculty_name)

        request_param = {"faculty" : faculty_name}
        available_programs = requests.get(BASE_URL + "programs", params = request_param).json()

        new_entities = []
        for program in available_programs:
            entity_value = EntityValueAndSynonyms(value = program)
            entity = Entity(name = entity_value)
            new_entities.append(entity)

        clear_dynamic_entities(handler_input, "CATCHALL")
        replace_dynamic_entities(handler_input, new_entities, "CATCHALL")

        speech_text = f"Your faculty is {faculty_name}. " + FACULTY_MESSAGES[MessageType.SPEECH]

        return rb.speak(speech_text).ask(FACULTY_MESSAGES[MessageType.REPROMPT]).response

    def handle_program(self, handler_input):
        rb = handler_input.response_builder
        program_name = get_canonical_value(handler_input, "text")

        if program_name == Status.NO_MATCH:
            speech_text = PROGRAM_MESSAGES[MessageType.ASK_AGAIN]
            return rb.speak(speech_text).ask(speech_text).response
        
        set_attribute(handler_input, "program", program_name)

        if get_attribute(handler_input, "question_type") == QuestionType.GENERAL:
            speech_text = f"Your program is {program_name}. " + PROGRAM_MESSAGES[MessageType.SPEECH]
        else:
            speech_text = f"Your program is {program_name}. " + PROGRAM_MESSAGES[MessageType.FIRST_SPECIFIC_QUESTION]
            
        clear_dynamic_entities(handler_input, "CATCHALL")

        return rb.speak(speech_text).ask(speech_text).response

    def load_specialization(self, handler_input):

        rb = handler_input.response_builder

        faculty_name = get_attribute(handler_input, "faculty")
        program_name = get_attribute(handler_input, "program")

        request_param = {
            "faculty" : faculty_name,
            "program" : program_name
        }
        available_specs = requests.get(BASE_URL + "specializations", params = request_param).json()

        new_entities = []
        
        spec_input = handler_input.request_envelope.request.intent.slots["text"]
        for spec in available_specs:
            regex = re.compile('[^a-zA-Z ]')
            spec_name = regex.sub('', spec.lower()).replace("  ", " ")
            if spec_input.value.lower() in spec_name:
                entity_value = EntityValueAndSynonyms(value = spec, synonyms = [spec_name])
                entity = Entity(name = entity_value)
                new_entities.append(entity)
        
        if not new_entities:
            speech_text = LOAD_SPEC_MESSAGES[MessageType.ASK_AGAIN]
            return rb.speak(speech_text).ask(speech_text).response
        elif len(new_entities) == 1:
            set_attribute(handler_input, "specialization", new_entities[0].name.value)
            replace_dynamic_entities(handler_input, YEAR_LEVEL_ENTITIES, "CATCHALL")
            speech_text = f"Your specialization is {new_entities[0].name.value}. " + LOAD_SPEC_MESSAGES[MessageType.SPEECH]
            return rb.speak(speech_text).ask(speech_text).response
        else:
            set_attribute(handler_input, "specialization", "loaded")
            speech_text = LOAD_SPEC_MESSAGES[MessageType.CONFIRM_SPEC]
        
        replace_dynamic_entities(handler_input, new_entities, "CATCHALL")

        return rb.speak(speech_text).ask(speech_text).response
    
    def handle_specialization(self, handler_input):
        rb = handler_input.response_builder
        specialization_name = get_canonical_value(handler_input, "text")

        if specialization_name == Status.NO_MATCH:
            speech_text = SPEC_MESSAGES[MessageType.ASK_AGAIN]
            return rb.speak(speech_text).ask(speech_text).response
        
        set_attribute(handler_input, "specialization", specialization_name)

        clear_dynamic_entities(handler_input, "CATCHALL")
        replace_dynamic_entities(handler_input, YEAR_LEVEL_ENTITIES, "CATCHALL")

        speech_text = f"Your specialization is {specialization_name}. " + SPEC_MESSAGES[MessageType.SPEECH]

        return (handler_input.response_builder
                .speak(speech_text)
                .ask(SPEC_MESSAGES[MessageType.REPROMPT])
                .response
        )
    
    def handle_year_level(self, handler_input):
        rb = handler_input.response_builder
        print(handler_input.request_envelope.request.intent.slots["text"].value)
        year_level = get_canonical_value(handler_input, "text")

        if year_level == Status.NO_MATCH:
            speech_text = YEAR_MESSAGES[MessageType.ASK_AGAIN]
            return rb.speak(speech_text).ask(speech_text).response
        
        set_attribute(handler_input, "year_level", year_level)

        clear_dynamic_entities(handler_input, "CATCHALL")

        speech_text = f"You are currently in your {year_level}. " + YEAR_MESSAGES[MessageType.SPEECH]
        return handler_input.response_builder.speak(speech_text).ask(speech_text).response

    def handle_topic(self, handler_input):
        topic = handler_input.request_envelope.request.intent.slots["text"].value
        set_attribute(handler_input, "topic", topic)

        speech_text = f"Your topic is {topic}. " + TOPIC_MESSAGES[MessageType.SPEECH]

        return handler_input.response_builder.speak(speech_text).ask(speech_text).response
    
    def handle_check_answer(self, handler_input):

        answer = get_attribute(handler_input, "answer")

        speech_text = answer if answer != Status.EMPTY else CHECK_ANS_MESSAGES[MessageType.ASK_AGAIN]
        speech_text += CHECK_ANS_MESSAGES[MessageType.SPEECH]

        replace_dynamic_entities(handler_input, YES_NO_ENTITIES, "CATCHALL")
        set_attribute(handler_input, "ask_another_question", Status.WAITING)
        
        return handler_input.response_builder.speak(speech_text).ask(speech_text).response

    def handle_question(self, handler_input):

        attributes = handler_input.attributes_manager.session_attributes
        question = handler_input.request_envelope.request.intent.slots["text"].value

        set_attribute(handler_input, "question", question)

        request_param = {
            "faculty" : attributes["faculty"],
            "program" : attributes["program"],
            "specialization" : attributes["specialization"] if is_specific(handler_input) else "",
            "year" : attributes["year_level"] if is_specific(handler_input) else "",
            "topic" : attributes["topic"],
            "question" : question,
        }

        request_id_holder = handler_input.request_envelope.request.request_id
        directive_header = Header(request_id = request_id_holder)
        speech = SpeakDirective(speech = QUESTION_MESSAGES[MessageType.PROGRESSIVE_RESPONSE])
        directive = SendDirectiveRequest(header = directive_header, directive = speech)
        directive_service_client = handler_input.service_client_factory.get_directive_service()
        directive_service_client.enqueue(directive)

        response = requests.get(BASE_URL + "question", params = request_param, timeout = 180).json()
        answer = response['main_response'] if response['main_response'] else Status.EMPTY

        set_attribute(handler_input, "answer", answer)

        speech_text = QUESTION_MESSAGES[MessageType.SPEECH]
        
        return handler_input.response_builder.speak(speech_text).ask(speech_text).response
    
    def handle_ask_another_question(self, handler_input):
        rb = handler_input.response_builder
        ask_another_question = get_canonical_value(handler_input, "text")

        if ask_another_question == Status.NO_MATCH:
            speech_text = ASK_ANOTHER_Q_MESSAGES[MessageType.ASK_AGAIN]
            return rb.speak(speech_text).ask(speech_text).response
        
        if ask_another_question == YesNo.NO:
            speech_text = ASK_ANOTHER_Q_MESSAGES[MessageType.GREETINGS]
            return rb.speak(speech_text).set_should_end_session(True).response
        
        slots = ["question_type", "question", "topic", "answer", "ask_another_question"]
        for slot in slots:
            set_attribute(handler_input, slot, Status.EMPTY)
        
        clear_dynamic_entities(handler_input, "CATCHALL")
        replace_dynamic_entities(handler_input, QUESTION_TYPE_ENTITIES, "CATCHALL")

        speech_text = ASK_ANOTHER_Q_MESSAGES[MessageType.SPEECH]

        return rb.speak(speech_text).ask(speech_text).response

sb.add_request_handler(LaunchRequestHandler())
sb.add_request_handler(CatchAllIntentHandler())

lambda_handler = sb.lambda_handler()