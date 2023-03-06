import attrs
from attrs import define
from typing import List, Optional
import github
import github.Issue
import github.Repository

@define
class Label:
    name: str
    _instance: Optional[github.Issue.Issue] = None
    _repo: Optional[github.Repository.Repository] = None

    @property
    def instance(self):
        if self._instance is None:
            self._instance = self._repo.get_label(self.name)
        return self._instance

    # setter
    def repo(self, newValue):
        self._repo = newValue
    repo = property(None, repo)


@define
class Labels:
    bug: Label
    feature: Label
    owners_approved: Label
    verification_required: Label
    design_elaboration_required: Label
    design: Label
    bounty: Label
    ideas_required: Label
    robot: Label
    postponed: Label
    waiting_author: Label

    difficulty_unreal: Label
    difficulty_very_hard: Label
    difficulty_hard: Label
    difficulty_easy: Label
    
    priority_max: Label
    priority_high: Label
    priority_low: Label


@define
class DiscordChannels:
    heads: int = None
    developers: int = None
    owners: int = None
    designers: int = None
    watchers: int = None


@define
class DiscordGuild:
    id: int
    channels: DiscordChannels = DiscordChannels()


@define
class Repository:
    name: str
    labels: Labels
    discord_guilds: Optional[List[DiscordGuild]]

    _instance: Optional[github.Repository.Repository] = None

    def init(self, github_api: github.Github):
        assert github_api
        self._instance = github_api.get_repo(self.name)
        label: Label
        for label in attrs.asdict(self.labels, recurse=False).values():
            label.repo = self._instance

    @property
    def instance(self):
        assert self._instance
