import asyncio
import logging
import os
from typing import Text

import matplotlib
import pytest

import rasa.utils.io
from rasa.core import train
from rasa.core.agent import Agent
from rasa.core.channels import channel
from rasa.core.channels.channel import CollectingOutputChannel, RestInput
from rasa.core.domain import Domain
from rasa.core.interpreter import RegexInterpreter
from rasa.core.nlg import TemplatedNaturalLanguageGenerator
from rasa.core.policies.ensemble import PolicyEnsemble, SimplePolicyEnsemble
from rasa.core.policies.memoization import (
    AugmentedMemoizationPolicy,
    MemoizationPolicy,
    Policy,
)
from rasa.core.processor import MessageProcessor
from rasa.core.slots import Slot
from rasa.core.tracker_store import InMemoryTrackerStore
from rasa.core.trackers import DialogueStateTracker
from rasa.train import train_async

matplotlib.use("Agg")

DEFAULT_DOMAIN_PATH_WITH_SLOTS = "data/test_domains/default_with_slots.yml"

DEFAULT_DOMAIN_PATH_WITH_MAPPING = "data/test_domains/default_with_mapping.yml"

DEFAULT_STORIES_FILE = "data/test_stories/stories_defaultdomain.md"

DEFAULT_STACK_CONFIG = "data/test_config/stack_config.yml"

DEFAULT_NLU_DATA = "examples/moodbot/data/nlu.md"

END_TO_END_STORY_FILE = "data/test_evaluations/end_to_end_story.md"

E2E_STORY_FILE_UNKNOWN_ENTITY = "data/test_evaluations/story_unknown_entity.md"

MOODBOT_MODEL_PATH = "examples/moodbot/models/"

DEFAULT_ENDPOINTS_FILE = "data/test_endpoints/example_endpoints.yml"

TEST_DIALOGUES = [
    "data/test_dialogues/default.json",
    "data/test_dialogues/formbot.json",
    "data/test_dialogues/moodbot.json",
    "data/test_dialogues/restaurantbot.json",
]

EXAMPLE_DOMAINS = [
    DEFAULT_DOMAIN_PATH_WITH_SLOTS,
    DEFAULT_DOMAIN_PATH_WITH_MAPPING,
    "examples/formbot/domain.yml",
    "examples/moodbot/domain.yml",
    "examples/restaurantbot/domain.yml",
]


class CustomSlot(Slot):
    def as_feature(self):
        return [0.5]


# noinspection PyAbstractClass,PyUnusedLocal,PyMissingConstructor
class ExamplePolicy(Policy):
    def __init__(self, example_arg):
        pass


@pytest.fixture
def loop():
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    loop = rasa.utils.io.enable_async_loop_debugging(loop)
    yield loop
    loop.close()


@pytest.fixture(scope="session")
def default_agent_path(default_agent, tmpdir_factory):
    path = tmpdir_factory.mktemp("agent").strpath
    default_agent.persist(path)
    return path


@pytest.fixture
def default_channel():
    return CollectingOutputChannel()


@pytest.fixture
async def default_processor(default_domain, default_nlg):
    agent = Agent(
        default_domain,
        SimplePolicyEnsemble([AugmentedMemoizationPolicy()]),
        interpreter=RegexInterpreter(),
    )

    training_data = await agent.load_data(DEFAULT_STORIES_FILE)
    agent.train(training_data)
    tracker_store = InMemoryTrackerStore(default_domain)
    return MessageProcessor(
        agent.interpreter,
        agent.policy_ensemble,
        default_domain,
        tracker_store,
        default_nlg,
    )


@pytest.fixture(scope="session")
def moodbot_domain(trained_moodbot_path):
    domain_path = os.path.join("examples", "moodbot", "domain.yml")
    return Domain.load(domain_path)


@pytest.fixture(scope="session")
def moodbot_metadata(unpacked_trained_moodbot_path):
    return PolicyEnsemble.load_metadata(
        os.path.join(unpacked_trained_moodbot_path, "core")
    )


@pytest.fixture
def default_nlg(default_domain):
    return TemplatedNaturalLanguageGenerator(default_domain.templates)


@pytest.fixture
def default_tracker(default_domain):
    return DialogueStateTracker("my-sender", default_domain.slots)
