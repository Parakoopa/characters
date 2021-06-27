from configcrunch import DocReference, load_subdocument, REMOVE
from schema import Schema, Optional

from char_sheets.config.specs import AbstractSpec
from char_sheets.config.specs._ogl_aware import OglAware
from char_sheets.config.specs.ref_dnd5e.dnd_weapon import DndWeapon


SKILL_MAP = {
    "Acrobatics": "dex",
    "Animal Handling": "wis",
    "Arcana": "int",
    "Athletics": "str",
    "Deception": "cha",
    "History": "int",
    "Insight": "wis",
    "Intimidation": "cha",
    "Investigation": "int",
    "Medicine": "wis",
    "Nature": "int",
    "Perception": "wis",
    "Performance": "cha",
    "Persuasion": "cha",
    "Religion": "int",
    "Sleight of Hand": "dex",
    "Stealth": "dex",
    "Survival": "wis",
}


def build_dnd_skills():
    skls = {}
    for name in SKILL_MAP.keys():
        skls[name] = {
            'proficiency': bool,
            Optional('expertise'): bool,
            Optional('boon'): int
        }
    return skls


class Dnd5eSpec(AbstractSpec, OglAware):
    @classmethod
    def header(cls) -> str:
        return "dnd5e"

    @classmethod
    def schema(cls) -> Schema:
        return Schema(
            {
                'background': str,
                'inspiration': int,
                'proficiency': int,
                'boons': {
                    'saves': {
                        'str': int,
                        'dex': int,
                        'con': int,
                        'int': int,
                        'wis': int,
                        'cha': int
                    }
                },
                'death_saves': {
                    'successes': int,
                    'fails': int,
                },
                'proficiencies': {
                    'weapons': {
                        'simple': bool,
                        'martial': bool,
                        'unarmed': bool
                    },
                    'armor': {
                        'light': bool,
                        'medium': bool,
                        'heavy': bool,
                        'shields': bool,
                    },
                    'saves': {
                        'str': bool,
                        'dex': bool,
                        'con': bool,
                        'int': bool,
                        'wis': bool,
                        'cha': bool
                    },
                },
                'weapons': [DocReference(DndWeapon)],
                'armor': {
                    'ac': int,
                    'name': str,
                    'stats': [str],
                },
                'skills': build_dnd_skills(),
            }
        )

    def _load_subdocuments(self, lookup_paths):
        if "weapons" in self.doc and self["weapons"] != REMOVE:
            lst = []
            for x in self["weapons"]:
                lst.append(load_subdocument(x, self, DndWeapon, lookup_paths))
            self["weapons"] = lst
        return self

    def ac(self):
        return self["armor"]["ac"] + self.armor_bonus()

    def passive_insight(self):
        return 10 + self.skill_bonus("Insight") + (5 if self["skills"]["Insight"]["proficiency"] else 0)

    def passive_investigation(self):
        return 10 + self.skill_bonus("Investigation") + (5 if self["skills"]["Investigation"]["proficiency"] else 0)

    def passive_perception(self):
        return 10 + self.skill_bonus("Perception") + (5 if self["skills"]["Perception"]["proficiency"] else 0)

    def armor_bonus(self):
        ac = 0
        for stat in self["armor"]["stats"]:
            ac += getattr(self.parent().parent().spec('ogl'), stat + '_m')()
        return ac

    def save_bonus(self, save):
        return getattr(self.parent().parent().spec('ogl'), save + '_m')() + (self['proficiency'] if self['proficiencies']['saves'][save] else 0)

    def skill_attribute(self, skill):
        return SKILL_MAP[skill]

    def skill_attribute_bonus(self, skill):
        return getattr(self.parent().parent().spec('ogl'), self.skill_attribute(skill) + '_m')()

    def skill_bonus(self, skill_name):
        return self.skill_attribute_bonus(skill_name) + \
               (self['proficiency'] if self['skills'][skill_name]['proficiency'] else 0) + \
               (self['proficiency'] if 'expertise' in self['skills'][skill_name] and self['skills'][skill_name]['expertise'] else 0) + \
               (self['skills'][skill_name]['boon'] if 'boon' in self['skills'][skill_name] else 0)

    def spellcast_dc(self):
        return 10 + getattr(self.parent().parent().spec('ogl'), self.parent().parent().spec('ogl')['spellcasting_mod'] + '_m')() + self['proficiency']