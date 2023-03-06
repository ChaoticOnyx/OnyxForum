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
    
    def stage_verification(self):
        query = self.in_repository() + \
            " " + self.open() + \
            " " + self.issue() + \
            " " + _include(self._labels.verification_required) + \
            " " + _exclude(self._labels.waiting_author) + \
            " " + _exclude(self._labels.postponed)
        
        return query
    
    def design_stage(self, priority=True):
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
    
    def development_stage(self, priority=True):
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
