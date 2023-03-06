from typing import List
from .repository import *

def _include(*labels: Label):
        assert len(labels)
        return "label:" + ','.join([f'"{label.name}"' for label in labels])

def _exclude(*labels: Label):
        assert len(labels)
        return "-label:" + ','.join([f'"{label.name}"' for label in labels])

class QueryGenerator:
    def __init__(self, repository):
        assert repository
        self.repository: Repository = repository

    @property 
    def _labels(self) -> Labels:
        return self.repository.labels

    def in_repository(self):
        return f"repo:{self.repository.name}"

    def open(self):
        return "is:open"

    def issue(self):
        return "is:issue"
    
    def pr(self):
        return "is:pr"
    
    def review_required(self):
        return "review:required"
    
    def not_assigned(self):
        return "no:assignee"

    def beginners(self):
        query =   self.in_repository() + \
            " " + self.open() + \
            " " + self.issue() + \
            " " + self.not_assigned() + \
            " " + _include(self._labels.difficulty_easy) + \
            " " + _exclude(self._labels.verification_required) + \
            " " + _exclude(self._labels.design_elaboration_required) + \
            " " + _exclude(self._labels.ideas_required) + \
            " " + _exclude(self._labels.postponed)
        
        return query
    
    def bounty(self):
        query =   self.in_repository() + \
            " " + self.open() + \
            " " + self.issue() + \
            " " + self.not_assigned() + \
            " " + _include(self._labels.bounty)
        
        return query

    def stage_owners(self, priority=True):
        query =   self.in_repository() + \
            " " + self.open() + \
            " " + self.issue() + \
            " " + _include(self._labels.feature) + \
            " " + _include(self._labels.design) + \
            " " + _exclude(self._labels.verification_required) + \
            " " + _exclude(self._labels.owners_approved) + \
            " " + _exclude(self._labels.design_elaboration_required) + \
            " " + _exclude(self._labels.ideas_required) + \
            " " + _exclude(self._labels.postponed)
        
        if priority:
            query += \
                " " + _include(self._labels.priority_high, self._labels.priority_max)
        
        return query
    
    def stage_owners_high_priority(self):
        return self.stage_owners() + " " + _include(self._labels.priority_high)
    
    def stage_owners_max_priority(self):
        return self.stage_owners() + " " + _include(self._labels.priority_max)
    
    def stage_verification(self):
        query = self.in_repository() + \
            " " + self.open() + \
            " " + self.issue() + \
            " " + _include(self._labels.verification_required) + \
            " " + _exclude(self._labels.waiting_author) + \
            " " + _exclude(self._labels.postponed)
        
        return query
    
    def stage_design(self, priority=True):
        query = self.in_repository() + \
            " " + self.open() + \
            " " + self.issue() + \
            " " + _include(self._labels.design_elaboration_required) + \
            " " + _exclude(self._labels.waiting_author) + \
            " " + _exclude(self._labels.postponed)
        
        if priority:
            query += \
                " " + _include(self._labels.priority_high, self._labels.priority_max)
        
        return query
    
    def stage_development_bugs(self):
        query = self.in_repository() + \
            " " + self.open() + \
            " " + self.issue() + \
            " " + _include(self._labels.bug) + \
            " " + _exclude(self._labels.verification_required) + \
            " " + _exclude(self._labels.waiting_author) + \
            " " + _exclude(self._labels.ideas_required) + \
            " " + _exclude(self._labels.design_elaboration_required) + \
            " " + _exclude(self._labels.postponed)
        
        return query
    
    def stage_development_bugs_high_priority(self):
        return self.stage_development_bugs() + " " + _include(self._labels.priority_high)
    
    def stage_development_bugs_max_priority(self):
        return self.stage_development_bugs() + " " + _include(self._labels.priority_max)
    
    def pr_review_required(self, priority=True):
        query = self.in_repository() + \
            " " + self.open() + \
            " " + self.pr() + \
            " " + self.review_required() + \
            " " + _exclude(self._labels.waiting_author) + \
            " " + _exclude(self._labels.postponed)
        
        if priority:
            query += \
                " " + _include(self._labels.priority_high, self._labels.priority_max)
        else:
            query += \
                " " + _exclude(self._labels.priority_high, self._labels.priority_max)

        return query
    
    def sprites(self):
        query = self.in_repository() + \
            " " + self.open() + \
            " " + self.issue() + \
            " " + _include(self._labels.sprite) + \
            " " + _exclude(self._labels.verification_required) + \
            " " + _exclude(self._labels.waiting_author) + \
            " " + _exclude(self._labels.ideas_required) + \
            " " + _exclude(self._labels.design_elaboration_required) + \
            " " + _exclude(self._labels.postponed)
        
        return query
    
    def sprites_high_priority(self):
        return self.sprites() + " " + _include(self._labels.priority_high)
    
    def sprites_max_priority(self):
        return self.sprites() + " " + _include(self._labels.priority_max)
