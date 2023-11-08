from ask_sdk_core.dispatch_components import AbstractRequestHandler
from ask_sdk_core.api_client import DefaultApiClient
from ask_sdk_core.utils import is_request_type, is_intent_name
from ask_sdk_core.skill_builder import CustomSkillBuilder
from ask_sdk_model.services.directive import (
    SendDirectiveRequest, Header, SpeakDirective)
from ask_sdk_model.dialog import DynamicEntitiesDirective
from ask_sdk_model.er.dynamic import UpdateBehavior, EntityListItem, Entity, EntityValueAndSynonyms
from ask_sdk_model.slu.entityresolution.status_code import StatusCode

import requests
import re

# Constants
BASE_URL = "http://student-advising-voice-assitant-demo.ca-central-1.elasticbeanstalk.com/"
ATTRIBUTES = ["question_type", "faculty", "program", "specialization", "year_level", "topic", "question", "answer", "ask_another_question"]
QUESTION_TYPE_ENTITIES = [
    Entity(name = EntityValueAndSynonyms(value = "general", synonyms = ["general question"])),
    Entity(name = EntityValueAndSynonyms(value = "specific", synonyms = ["specific question", "program specific question", "program specific"])),
]
YEAR_LEVEL_ENTITIES = [
    Entity(name = EntityValueAndSynonyms(value = "First Year", synonyms = ["one", "1st year", "freshman", "first year"])),
    Entity(name = EntityValueAndSynonyms(value = "Second Year", synonyms = ["two", "2nd year", "sophomore", "second year"])),
    Entity(name = EntityValueAndSynonyms(value = "Third Year", synonyms = ["three", "3rd year", "junior", "third year"])),
    Entity(name = EntityValueAndSynonyms(value = "Fourth Year", synonyms = ["four", "4th year", "senior", "fourth year"])),
    Entity(name = EntityValueAndSynonyms(value = "Fifth Year", synonyms = ["five", "5th year", "graduate", "fifth year"])),
]

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
'''
def get_canonical_value(handler_input, slot_name):
        input = handler_input.request_envelope.request.intent.slots[slot_name].resolutions.resolutions_per_authority[1]
        print(input.status.code)
        return "no match" if input.status.code == StatusCode.ER_SUCCESS_NO_MATCH else input.values[0].value.name

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
    return get_attribute(handler_input, "faculty") == "" and get_attribute(handler_input, "program") == ""
    
def is_first_specific_question(handler_input):
    return get_attribute(handler_input, "question_type") == "specific" and get_attribute(handler_input, "specialization") == "" and get_attribute(handler_input, "year_level") == ""

def add_faculty_entities(handler_input):
    faculties = requests.get(BASE_URL + "faculties").json()
    print(faculties)
    new_entities = []
    for faculty in faculties:
        entity_value = EntityValueAndSynonyms(value = faculty, synonyms = [faculty.lower(), faculty.lower().replace('the ', '')])
        entity = Entity(name = entity_value)
        new_entities.append(entity)
    replace_dynamic_entities(handler_input, new_entities, "CATCHALL")

    return "OK. Now please tell me your faculty."


# Request Handlers
class LaunchRequestHandler(AbstractRequestHandler):

    def can_handle(self, handler_input):
        return is_request_type("LaunchRequest")(handler_input)
    
    def handle(self, handler_input):

        self.initialize_session_attributes(handler_input)

        speech_text = "Welcome to Student Advising Assistant!! Do you want to ask a general question or program-specific question?"
        reprompt_text = "Please tell me what type of question you want to ask."

        replace_dynamic_entities(handler_input, QUESTION_TYPE_ENTITIES, "CATCHALL")
        
        return handler_input.response_builder.speak(speech_text).ask(reprompt_text).set_should_end_session(False).response
    
    def initialize_session_attributes(self, handler_input):
        for attribute in ATTRIBUTES:
            set_attribute(handler_input, attribute, "")

class CatchAllIntentHandler(AbstractRequestHandler):
    def can_handle(self, handler_input):
        return is_intent_name("CatchAllIntent")(handler_input)
    
    def handle(self, handler_input):
        if get_attribute(handler_input, "question_type") == "":
            return self.handle_question_type(handler_input)
        elif get_attribute(handler_input, "faculty") == "":
            return self.handle_faculty(handler_input)
        elif get_attribute(handler_input, "program") == "":
            return self.handle_program(handler_input)
        elif get_attribute(handler_input, "question_type") == "specific" and get_attribute(handler_input, "specialization") == "":
            return self.load_specialization(handler_input) 
        elif get_attribute(handler_input, "specialization") == "loaded":
            return self.handle_specialization(handler_input)
        elif get_attribute(handler_input, "question_type") == "specific" and get_attribute(handler_input, "year_level") == "":
            return self.handle_year_level(handler_input)
        elif get_attribute(handler_input, "topic") == "":
            return self.handle_topic(handler_input)
        elif get_attribute(handler_input, "ask_another_question") == "waiting":
            return self.handle_ask_another_question(handler_input)
        elif get_attribute(handler_input, "question") != "":
            return self.handle_check_answer(handler_input)
        else:
            return self.handle_question(handler_input)
    
    def handle_question_type(self, handler_input):
        rb = handler_input.response_builder
        question_type = get_canonical_value(handler_input, "text")

        if question_type == "no match":
            speech_text = "Sorry, I didn't get that. Please tell me if you want to ask a general question or program-specific question."
            return rb.speak(speech_text).ask(speech_text).response

        set_attribute(handler_input, "question_type", question_type)
        clear_dynamic_entities(handler_input, "CATCHALL")

        if is_first_question(handler_input):
            speech_text = add_faculty_entities(handler_input)
        elif is_first_specific_question(handler_input):
            speech_text = "OK. Please tell me your field of study."
        else:
            speech_text = "OK. Please tell me the topic of your question."

        return rb.speak(speech_text).ask(speech_text).response
    
    def handle_faculty(self, handler_input):
        rb = handler_input.response_builder
        faculty_name = get_canonical_value(handler_input, "text")

        if faculty_name == "no match":
            speech_text = "Sorry, I didn't get that. Please tell me your faculty again."
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

        speech_text = f"Your faculty is {faculty_name}. What is your program?"
        reprompt_text = "What is your program?"

        return rb.speak(speech_text).ask(reprompt_text).response

    def handle_program(self, handler_input):
        rb = handler_input.response_builder
        program_name = get_canonical_value(handler_input, "text")

        if program_name == "no match":
            speech_text = "Sorry, I didn't get that. Please tell me your program again."
            return rb.speak(speech_text).ask(speech_text).response
        
        set_attribute(handler_input, "program", program_name)

        if get_attribute(handler_input, "question_type") == "general":
            speech_text = f"Your program is {program_name}. What is the topic of your question?"
        else:
            speech_text = f"Your program is {program_name}. What is your field of study?"
            
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
            speech_text = "Sorry, I could not find any specialization that matches your input. Please try again."
            return rb.speak(speech_text).ask(speech_text).response
        elif len(new_entities) == 1:
            set_attribute(handler_input, "specialization", new_entities[0].name.value)
            replace_dynamic_entities(handler_input, YEAR_LEVEL_ENTITIES, "CATCHALL")
            speech_text = f"Your specialization is {new_entities[0].name.value}. What is your year level?"
            return rb.speak(speech_text).ask(speech_text).response
        else:
            set_attribute(handler_input, "specialization", "loaded")
            speech_text = "I have loaded the specialization options. Please tell me your specialization."
        
        replace_dynamic_entities(handler_input, new_entities, "CATCHALL")

        return rb.speak(speech_text).ask(speech_text).response
    
    def handle_specialization(self, handler_input):
        rb = handler_input.response_builder
        specialization_name = get_canonical_value(handler_input, "text")

        if specialization_name == "no match":
            speech_text = "Sorry, I didn't get that. Please tell me your specialization again."
            return rb.speak(speech_text).ask(speech_text).response
        
        set_attribute(handler_input, "specialization", specialization_name)

        year_level_entities = [
            Entity(name = EntityValueAndSynonyms(value = "First Year", synonyms = ["one", "1st year", "freshman", "first year"])),
            Entity(name = EntityValueAndSynonyms(value = "Second Year", synonyms = ["two", "2nd year", "sophomore", "second year"])),
            Entity(name = EntityValueAndSynonyms(value = "Third Year", synonyms = ["three", "3rd year", "junior", "third year"])),
            Entity(name = EntityValueAndSynonyms(value = "Fourth Year", synonyms = ["four", "4th year", "senior", "fourth year"])),
            Entity(name = EntityValueAndSynonyms(value = "Fifth Year", synonyms = ["five", "5th year", "graduate", "fifth year"])),
        ]

        clear_dynamic_entities(handler_input, "CATCHALL")
        replace_dynamic_entities(handler_input, YEAR_LEVEL_ENTITIES, "CATCHALL")

        speech_text = f"Your specialization is {specialization_name}. Please tell me your year level."
        reprompt_text = "Please tell me your year level."

        return handler_input.response_builder.speak(speech_text).ask(reprompt_text).response

    def handle_year_level(self, handler_input):
        rb = handler_input.response_builder
        print(handler_input.request_envelope.request.intent.slots["text"].value)
        year_level = get_canonical_value(handler_input, "text")

        if year_level == "no match":
            speech_text = "Sorry, I didn't get that. Please tell me your year level again."
            return rb.speak(speech_text).ask(speech_text).response
        
        set_attribute(handler_input, "year_level", year_level)

        clear_dynamic_entities(handler_input, "CATCHALL")

        speech_text = f"You are currently in your {year_level}. Now please tell me the topic of your question."
        return handler_input.response_builder.speak(speech_text).ask(speech_text).response

    def handle_topic(self, handler_input):
        topic = handler_input.request_envelope.request.intent.slots["text"].value
        set_attribute(handler_input, "topic", topic)

        speech_text = f"Your topic is {topic}. Please tell me your question."

        return handler_input.response_builder.speak(speech_text).ask(speech_text).response
    
    def handle_check_answer(self, handler_input):

        answer = get_attribute(handler_input, "answer")

        speech_text = answer if answer != "" else "Sorry, I could not find any answer for your question."
        speech_text += "<break time='3s' /> Do you want to ask another question?"

        new_entities = [
            Entity(name = EntityValueAndSynonyms(value = "yes", synonyms = ["yeah", "yep", "I do", "yes please", "you know it"])),
            Entity(name = EntityValueAndSynonyms(value = "no", synonyms = ["nope", "no thank you", "I don't", "I do not"])),
        ]
        replace_dynamic_entities(handler_input, new_entities, "CATCHALL")
        set_attribute(handler_input, "ask_another_question", "waiting")
        
        return handler_input.response_builder.speak(speech_text).ask(speech_text).response

    def handle_question(self, handler_input):

        attributes = handler_input.attributes_manager.session_attributes
        question = handler_input.request_envelope.request.intent.slots["text"].value

        set_attribute(handler_input, "question", question)

        request_param = {
            "faculty" : attributes["faculty"],
            "program" : attributes["program"],
            "specialization" : attributes["specialization"] if get_attribute(handler_input, "question_type") == "specific" else "",
            "year" : attributes["year_level"] if get_attribute(handler_input, "question_type") == "specific" else "",
            "topic" : attributes["topic"],
            "question" : question,
        }

        request_id_holder = handler_input.request_envelope.request.request_id
        directive_header = Header(request_id = request_id_holder)
        speech = SpeakDirective(speech = "Your question has been recorded. Please wait a moment while I generate the answer. <break time='10s' /> The answer is ready. Please ask 'Alexa, check answer.' to check the answer.")
        directive = SendDirectiveRequest(header = directive_header, directive = speech)
        directive_service_client = handler_input.service_client_factory.get_directive_service()
        directive_service_client.enqueue(directive)

        response = requests.get(BASE_URL + "question", params = request_param, timeout = 180).json()
        answer = response['main_response'] if response['main_response'] else ""

        set_attribute(handler_input, "answer", answer)

        speech_text = "Your answer is ready. Please ask 'check answer' to check your answer."
        
        return handler_input.response_builder.speak(speech_text).ask(speech_text).response
    
    def handle_ask_another_question(self, handler_input):
        rb = handler_input.response_builder
        ask_another_question = get_canonical_value(handler_input, "text")

        if ask_another_question == "no match":
            speech_text = "Sorry, I didn't get that. Please answer either yes or no."
            return rb.speak(speech_text).ask(speech_text).response
        
        if ask_another_question == "no":
            speech_text = "Thank you for using the Student Advising Assistant. Goodbye!"
            return rb.speak(speech_text).set_should_end_session(True).response
        
        slots = ["question_type", "question", "topic", "answer", "ask_another_question"]
        for slot in slots:
            set_attribute(handler_input, slot, "")
        
        clear_dynamic_entities(handler_input, "CATCHALL")
        replace_dynamic_entities(handler_input, QUESTION_TYPE_ENTITIES, "CATCHALL")

        speech_text = "Great!! Please tell me if you want to ask a general question or a program specific question."

        return rb.speak(speech_text).ask(speech_text).response

sb.add_request_handler(LaunchRequestHandler())
sb.add_request_handler(CatchAllIntentHandler())

lambda_handler = sb.lambda_handler()