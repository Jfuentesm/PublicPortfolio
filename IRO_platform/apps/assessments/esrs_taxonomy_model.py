class ESRSClassification:
    def __init__(self):
        self.topics = {
            'ESRS E1': {
                'Topic': 'Climate change',
                'Sub topics': [
                    'Climate change adaptation',
                    'Climate change mitigation',
                    'Energy'
                ]
            },
            'ESRS E2': {
                'Topic': 'Pollution',
                'Sub topics': [
                    'Pollution of air',
                    'Pollution of water',
                    'Pollution of soil',
                    'Pollution of living organisms and food resources',
                    'Substances of concern',
                    'Substances of very high concern',
                    'Microplastics'
                ]
            },
            'ESRS E3': {
                'Topic': 'Water and marine resources',
                'Sub topics': [
                    'Water',
                    'Marine resources'
                ],
                'Details': {
                    'Water': [
                        'Water consumption',
                        'Water withdrawals',
                        'Water discharges'
                    ],
                    'Marine resources': [
                        'Water discharges in the oceans',
                        'Extraction and use of marine resources'
                    ]
                }
            },
            'ESRS E4': {
                'Topic': 'Biodiversity and ecosystems',
                'Sub topics': [
                    'Direct impact drivers of biodiversity loss',
                    'Impacts on the state of species',
                    'Impacts on the extent and condition of ecosystems',
                    'Impacts and dependencies on ecosystem services'
                ],
                'Details': {
                    'Direct impact drivers of biodiversity loss': [
                        'Climate Change',
                        'Land-use change, fresh water-use change and sea-use change',
                        'Direct exploitation',
                        'Invasive alien species',
                        'Pollution',
                        'Others'
                    ],
                    'Impacts on the state of species': [
                        'Species population size',
                        'Species global extinction risk'
                    ],
                    'Impacts on the extent and condition of ecosystems': [
                        'Land degradation',
                        'Desertification',
                        'Soil sealing'
                    ]
                }
            },
            'ESRS E5': {
                'Topic': 'Circular economy',
                'Sub topics': [
                    'Resources inflows, including resource use',
                    'Resource outflows related to products and services',
                    'Waste'
                ]
            },
            'ESRS S1': {
                'Topic': 'Own workforce',
                'Sub topics': [
                    'Working conditions',
                    'Equal treatment and opportunities for all',
                    'Other work-related rights'
                ],
                'Details': {
                    'Working conditions': [
                        'Secure employment',
                        'Working time',
                        'Adequate wages',
                        'Social dialogue',
                        'Freedom of association, the existence of works councils, and the information, consultation, and participation rights of workers',
                        'Collective bargaining, including rate of workers covered by collective agreements',
                        'Work-life balance',
                        'Health and safety'
                    ],
                    'Equal treatment and opportunities for all': [
                        'Gender equality and equal pay for work of equal value',
                        'Training and skills development',
                        'Employment and inclusion of persons with disabilities',
                        'Measures against violence and harassment in the workplace',
                        'Diversity'
                    ],
                    'Other work-related rights': [
                        'Child labour',
                        'Forced labour',
                        'Adequate housing',
                        'Privacy'
                    ]
                }
            },
            'ESRS S2': {
                'Topic': 'Workers in the value chain',
                'Sub topics': [
                    'Working conditions',
                    'Equal treatment and opportunities for all',
                    'Other work-related rights'
                ],
                'Details': {
                    'Working conditions': [
                        'Secure employment',
                        'Working time',
                        'Adequate wages',
                        'Social dialogue',
                        'Freedom of association, including the existence of work councils',
                        'Collective bargaining',
                        'Work-life balance',
                        'Health and safety'
                    ],
                    'Equal treatment and opportunities for all': [
                        'Gender equality and equal pay for work of equal value',
                        'Training and skills development',
                        'Employment and inclusion of persons with disabilities',
                        'Measures against violence and harassment in the workplace',
                        'Diversity'
                    ],
                    'Other work-related rights': [
                        'Child labour',
                        'Forced labour',
                        'Adequate housing',
                        'Water and sanitation',
                        'Privacy'
                    ]
                }
            },
            'ESRS S3': {
                'Topic': 'Affected communities',
                'Sub topics': [
                    'Communities\' economic, social, and cultural rights',
                    'Communities\' civil and political rights',
                    'Rights of indigenous peoples'
                ],
                'Details': {
                    'Communities\' economic, social, and cultural rights': [
                        'Adequate housing',
                        'Adequate food',
                        'Water and sanitation',
                        'Land-related impacts',
                        'Security-related impacts'
                    ],
                    'Communities\' civil and political rights': [
                        'Freedom of expression',
                        'Freedom of assembly',
                        'Impacts on human rights defenders'
                    ],
                    'Rights of indigenous peoples': [
                        'Free, prior, and informed consent',
                        'Self-determination',
                        'Cultural rights'
                    ]
                }
            },
            'ESRS S4': {
                'Topic': 'Consumers and end-users',
                'Sub topics': [
                    'Information-related impacts for consumers and/or end-users',
                    'Personal safety of consumers and/or end-users',
                    'Social inclusion of consumers and/or end-users'
                ],
                'Details': {
                    'Information-related impacts for consumers and/or end-users': [
                        'Privacy',
                        'Freedom of expression',
                        'Access to (quality) information'
                    ],
                    'Personal safety of consumers and/or end-users': [
                        'Health and safety',
                        'Security of a person',
                        'Protection of children'
                    ],
                    'Social inclusion of consumers and/or end-users': [
                        'Non-discrimination',
                        'Access to products and services',
                        'Responsible marketing practices'
                    ]
                }
            },
            'ESRS G1': {
                'Topic': 'Business conduct',
                'Sub topics': [
                    'Corporate culture',
                    'Protection of whistle-blowers',
                    'Animal welfare',
                    'Political engagement and lobbying activities',
                    'Management of relationships with suppliers including payment practices',
                    'Corruption and bribery'
                ],
                'Details': {
                    'Corruption and bribery': [
                        'Prevention and detection including training',
                        'Incident'
                    ]
                }
            }
        }
    
    def get_topic(self, esrs_code):
        if esrs_code in self.topics:
            return self.topics[esrs_code]['Topic']
        return None
    
    def get_subtopics(self, esrs_code):
        if esrs_code in self.topics:
            return self.topics[esrs_code]['Sub topics']
        return None
    
    def get_details(self, esrs_code, subtopic):
        if esrs_code in self.topics and 'Details' in self.topics[esrs_code]:
            if subtopic in self.topics[esrs_code]['Details']:
                return self.topics[esrs_code]['Details'][subtopic]
        return None
    
    def display_full_classification(self):
        for code, data in self.topics.items():
            print(f"{code}: {data['Topic']}")
            
            for subtopic in data['Sub topics']:
                print(f"  - {subtopic}")
                
                if 'Details' in data and subtopic in data['Details']:
                    for detail in data['Details'][subtopic]:
                        print(f"    * {detail}")
