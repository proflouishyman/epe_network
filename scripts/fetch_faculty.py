#!/usr/bin/env python3
"""
fetch_faculty.py — scrape each EPE center's people/faculty page and write
data/individuals.json.  Run from the project root:
    python3 scripts/fetch_faculty.py
"""

import json, re, time, unicodedata
from pathlib import Path
from urllib.request import urlopen, Request
from urllib.error import URLError, HTTPError
from html.parser import HTMLParser

ROOT = Path(__file__).parent.parent
OUT  = ROOT / 'data' / 'individuals.json'
TODAY = '2026-06-30'

# ── Center metadata ────────────────────────────────────────────────────────────
CENTERS = {
    'cebrap':         dict(name='Brazilian Center of Analysis and Planning (CEBRAP)',
                           institution='CEBRAP (independent research center)',
                           country='Brazil', region='Latin America'),
    'cede-uniandes':  dict(name='Center for Studies on Economic Development (CEDE)',
                           institution='Universidad de los Andes',
                           country='Colombia', region='Latin America'),
    'auc-mena':       dict(name='Pathways Beyond Neoliberalism: Voices from MENA',
                           institution='American University in Cairo',
                           country='Egypt', region='MENA'),
    'iitb-npe':       dict(name='New Political Economy Initiative (NPEI)',
                           institution='Indian Institute of Technology Bombay',
                           country='India', region='South/Southeast Asia'),
    'colmex-pae':     dict(name='Program for the Economic Analysis of Mexico (PREA)',
                           institution='El Colegio de México',
                           country='Mexico', region='Latin America'),
    'wits-scis':      dict(name='Southern Centre for Inequality Studies (SCIS)',
                           institution='University of the Witwatersrand',
                           country='South Africa', region='Africa'),
    'lse-rcc':        dict(name='Reimagining Cohesive Capitalism',
                           institution='London School of Economics',
                           country='United Kingdom', region='Europe'),
    'ucl-iipp':       dict(name='Institute for Innovation and Public Purpose (IIPP)',
                           institution='University College London',
                           country='United Kingdom', region='Europe'),
    'columbia-ccpe':  dict(name='Columbia Center for Political Economy',
                           institution='Columbia University',
                           country='United States', region='North America'),
    'harvard-rie':    dict(name='Reimagining the Economy Initiative',
                           institution='Harvard Kennedy School',
                           country='United States', region='North America'),
    'howard-cees':    dict(name='Center for Equitable Economy and Sustainable Society',
                           institution='Howard University',
                           country='United States', region='North America'),
    'ces-jhu':        dict(name='Center on Economy and Society',
                           institution='Johns Hopkins University',
                           country='United States', region='North America'),
    'mit-sfw':        dict(name='Work of the Future',
                           institution='MIT',
                           country='United States', region='North America'),
    'sfi-epe':        dict(name='Emergent Political Economies',
                           institution='Santa Fe Institute',
                           country='United States', region='North America'),
    'besi-berkeley':  dict(name='Berkeley Economy and Society Initiative (BESI)',
                           institution='UC Berkeley',
                           country='United States', region='North America'),
}

# ── People to seed — compiled from workflow scraping results ───────────────────
# Format: (name, title, email, website)
PEOPLE = {
    'cebrap': [
        ('Adrian Gurza Lavalle', 'Director; Professor of Political Science', '', ''),
        ('Flávia Melo', 'Researcher', '', ''),
        ('Lara Cavalcante', 'Researcher', '', ''),
        ('João Paulo Candia Veiga', 'Researcher', '', ''),
        ('Vera Schattan Coelho', 'Senior Researcher', '', ''),
        ('Marta Arretche', 'Senior Researcher; Professor, USP', '', ''),
        ('Gisela Taschner', 'Researcher', '', ''),
        ('Renato Colistete', 'Researcher; Professor, FEA-USP', '', ''),
    ],
    'cede-uniandes': [
        ('Marc Hofstetter', 'Director; Professor of Economics', '', ''),
        ('Raquel Bernal', 'Professor of Economics', '', ''),
        ('Alejandro Gaviria', 'Professor of Economics', '', ''),
        ('Alejandro Sánchez', 'Associate Researcher', '', ''),
        ('Ana María Iregui', 'Professor of Economics', '', ''),
        ('Adriana Camacho', 'Professor of Economics', '', ''),
        ('Carlos Medina', 'Researcher', '', ''),
        ('Darío Maldonado', 'Professor of Economics', '', ''),
        ('Fabio Sánchez', 'Professor of Economics', '', ''),
        ('Felipe Barrera-Osorio', 'Professor of Economics', '', ''),
        ('Juan Carlos Rodríguez', 'Professor of Economics', '', ''),
        ('Juan Guillermo Bedoya', 'Researcher', '', ''),
        ('Leopoldo Fergusson', 'Professor of Economics', '', ''),
        ('Marcela Eslava', 'Professor of Economics', '', ''),
        ('María Angélica Bautista', 'Researcher', '', ''),
        ('Mauricio Romero', 'Associate Professor of Economics', '', ''),
        ('Pablo Querubín', 'Professor of Economics', '', ''),
        ('Pamela Medina', 'Researcher', '', ''),
        ('Santiago Saavedra', 'Associate Professor of Economics', '', ''),
        ('Sergio Chaparro', 'Researcher', '', ''),
    ],
    'auc-mena': [
        ('Amr Adly', 'Principal Investigator; Associate Professor of Political Science', '', ''),
        ('Ibrahim Awad', 'Co-Principal Investigator; Professor', '', ''),
        ('Dina Makram-Ebeid', 'Researcher; Associate Professor', '', ''),
        ('Nouran El-Behairy', 'Research Coordinator', '', ''),
    ],
    'iitb-npe': [
        ('Anush Kapadia', 'Director; Associate Professor, Humanities and Social Sciences', 'akapadia@iitb.ac.in', ''),
        ('Rahul Lahoti', 'Researcher', '', ''),
        ('Ananta Gupta', 'Researcher', '', ''),
        ('Himanshu', 'Affiliated Researcher; Associate Professor, Jawaharlal Nehru University', '', ''),
        ('J. Devika', 'Affiliated Researcher; Professor, Centre for Development Studies', '', ''),
        ('Shalini Randeria', 'Affiliated Researcher; Rector, IWM Vienna', '', ''),
        ('Rina Agarwala', 'Affiliated Researcher; Professor, Johns Hopkins University', '', ''),
        ('Balakrishnan Rajagopal', 'Affiliated Researcher; Professor, MIT', '', ''),
        ('Amita Baviskar', 'Affiliated Researcher; Professor, Ashoka University', '', ''),
        ('Jomo Kwame Sundaram', 'Affiliated Researcher; Former UN Assistant Secretary-General', '', ''),
        ('Pranab Bardhan', 'Affiliated Researcher; Emeritus Professor, UC Berkeley', '', ''),
        ('Jayati Ghosh', 'Affiliated Researcher; Professor, University of Massachusetts Amherst', '', ''),
        ('Neera Chandhoke', 'Affiliated Researcher; Emeritus Professor, Delhi University', '', ''),
        ('Achin Vanaik', 'Affiliated Researcher', '', ''),
    ],
    'colmex-pae': [
        ('Laura Juárez González', 'Program Coordinator', '', ''),
        ('Arturo Antón Sarabia', 'Professor of Economics', '', ''),
        ('Alejandro Castañeda', 'Professor of Economics', '', ''),
        ('Noel Maurer', 'Professor', '', ''),
        ('Raul De La Rosa', 'Professor of Economics', '', ''),
        ('Gerardo Esquivel', 'Professor of Economics', '', ''),
        ('Juan Carlos Moreno-Brid', 'Professor of Economics', '', ''),
        ('Ariel Ruiz Euler', 'Researcher', '', ''),
        ('Diana Terrazas', 'Researcher', '', ''),
        ('Enrique Cardenas', 'Professor of Economics', '', ''),
        ('Héctor Pérez Gómez', 'Researcher', '', ''),
        ('Isabel Sáinz Pardo', 'Researcher', '', ''),
        ('Pablo Cotler', 'Professor of Economics', '', ''),
    ],
    'wits-scis': [
        ('Imraan Valodia', 'Director; Pro Vice-Chancellor for Climate, Sustainability and Inequality', '', ''),
        ('Gilad Isaacs', 'Senior Researcher', '', ''),
        ('Klara Nahrgang', 'Researcher', '', ''),
        ('Murray Leibbrandt', 'Professor; SALDRU Director', '', ''),
        ('Arabo Ewinyu', 'Researcher', '', ''),
        ('Neva Makgetla', 'Senior Researcher', '', ''),
        ('Leilanie Swart', 'Researcher', '', ''),
        ('Ndikho Mtukushe', 'Researcher', '', ''),
        ('Phumzile Ncube', 'Researcher', '', ''),
        ('Simone Schotte', 'Researcher', '', ''),
        ('Tanya Goldman', 'Researcher', '', ''),
        ('Alexes Tekane', 'Researcher', '', ''),
        ('Aroop Chatterjee', 'Researcher', '', ''),
    ],
    'lse-rcc': [
        ('Tim Besley', 'Co-Director; Professor of Economics and Political Science', '', ''),
        ('Daniel Chandler', 'Co-Director; Research Fellow', '', ''),
        ('Torsten Persson', 'Affiliated Researcher; Professor', '', ''),
        ('Philipp Ulrich', 'Research Officer', '', ''),
    ],
    'ucl-iipp': [
        ('Mariana Mazzucato', 'Founding Director; Professor of Economics of Innovation and Public Value', 'iipp-dir-comms@ucl.ac.uk', ''),
        ('Carlota Perez', 'Honorary Professor; Affiliated Scholar', '', ''),
        ('Rainer Kattel', 'Deputy Director; Professor of Innovation and Public Governance', '', ''),
        ('Josh Ryan-Collins', 'Associate Professor in Economics and Finance', '', ''),
        ('Caetano Penna', 'Associate Professor', '', ''),
        ('Anna Valero', 'Associate Professor', '', ''),
        ('Marco Steinberg', 'Affiliated Researcher', '', ''),
        ('Laurie Macfarlane', 'Research Associate', '', ''),
        ('Henry Lishi Li', 'Research Associate', '', ''),
        ('Michael Jacobs', 'Honorary Professor; Affiliated Policy Fellow', '', ''),
        ('Kate Raworth', 'Affiliated Senior Researcher', '', ''),
        ('Iana Lyadze', 'Research Fellow', '', ''),
        ('Matteo Deleidi', 'Affiliated Researcher', '', ''),
        ('Carolina Alves', 'Research Fellow', '', ''),
        ('Gregor Semieniuk', 'Research Fellow', '', ''),
        ('Pedro Cantú', 'Researcher', '', ''),
        ('Ada Biolcati-Rinaldi', 'Researcher', '', ''),
        ('Giorgos Gouzoulis', 'Research Fellow', '', ''),
        ('Sabrina Ferretti', 'Research Fellow', '', ''),
        ('Louise Dalingwater', 'Affiliated Researcher', '', ''),
    ],
    'columbia-ccpe': [
        ('Suresh Naidu', 'Co-Director; Professor of Economics and International and Public Affairs', '', ''),
        ('Shom Mazumder', 'Co-Director; Assistant Professor of Political Science', '', ''),
        ('Mark Lilla', 'Affiliated Faculty; Professor of Humanities', '', ''),
        ('Belinda Davis', 'Affiliated Faculty; Professor of History', '', ''),
        ('Ira Katznelson', 'Affiliated Faculty; Ruggles Professor of Political Science and History', '', ''),
        ('Alessandra Casella', 'Affiliated Faculty; Professor of Economics', '', ''),
        ('Dorian Warren', 'Affiliated Scholar', '', ''),
        ('Damon Jones', 'Affiliated Researcher; Professor of Economics, UChicago', '', ''),
        ('Naomi Lamoreaux', 'Affiliated Faculty; Professor of History and Economics, Yale', '', ''),
        ('Niko Matouschek', 'Affiliated Researcher; Professor, Northwestern Kellogg', '', ''),
        ('Pavithra Suryanarayan', 'Affiliated Faculty; Assistant Professor of Political Science', '', ''),
        ('Raymond Fisman', 'Affiliated Researcher; Professor, Boston University', '', ''),
        ('Subroto Roy', 'Researcher', '', ''),
        ('Victoria Nuguer', 'Affiliated Researcher', '', ''),
    ],
    'harvard-rie': [
        ('Dani Rodrik', 'Faculty Co-Director; Ford Foundation Professor of International Political Economy', '', ''),
        ('Gordon Hanson', 'Faculty Co-Director; Peter Wertheim Professor of Urban Policy', '', ''),
        ('Rohan Sandhu', 'Executive Director', '', ''),
        ('Alexandra Mitric', 'Research Director', '', ''),
        ('Carmen Reinhart', 'Affiliated Faculty; Professor of the International Financial System', '', ''),
        ('Stefanie Stantcheva', 'Affiliated Faculty; Professor of Economics', '', ''),
        ('Lawrence Katz', 'Affiliated Faculty; Professor of Economics', '', ''),
        ('Claudia Goldin', 'Affiliated Faculty; Professor of Economics', '', ''),
        ('Robert Lawrence', 'Affiliated Faculty; Professor of International Trade and Investment', '', ''),
    ],
    'howard-cees': [
        ('Michael Ralph', 'Founding Director; Cameron Schrier Professor, Afro-American Studies', '', ''),
        ('Jevay Grooms', 'Co-Director; Associate Professor of Economics', 'jevay.grooms@howard.edu', ''),
        ('Darrick Hamilton', 'Affiliated Scholar; Professor of Economics and Urban Policy, The New School', '', ''),
        ('Olugbenga Ajilore', 'Affiliated Researcher', '', ''),
        ('Valerie Wilson', 'Affiliated Researcher; Director of Program on Race, Ethnicity, and the Economy, EPI', '', ''),
    ],
    'ces-jhu': [
        ('Louis Hyman', 'Director; Professor', 'lhyman6@jh.edu', 'www.louishyman.com'),
        ('Angus Burgin', 'Affiliated Faculty; Associate Professor of History', '', ''),
        ('Ling Chen', 'Affiliated Faculty; Associate Professor of Political Economy', '', ''),
        ('Henry Farrell', 'Affiliated Faculty; Professor of International Affairs', '', ''),
        ('Elias Stein', 'Affiliated Researcher', '', ''),
        ('Alfredo Saad-Filho', 'Affiliated Faculty; Professor of Political Economy', '', ''),
        ('Margaret Levi', 'Advisory Board Chair; Professor, Stanford University', '', ''),
    ],
    'mit-sfw': [
        ('Julie Shah', 'Director; Professor, Aeronautics and Astronautics', '', ''),
        ('David Autor', 'Affiliated Faculty; Ford Professor of Economics', '', ''),
        ('Paul Osterman', 'Affiliated Faculty; Professor, Sloan School of Management', '', ''),
        ('Nathan Wilmers', 'Affiliated Faculty; Assistant Professor, Sloan School of Management', '', ''),
        ('Daron Acemoglu', 'Affiliated Faculty; Institute Professor of Economics', '', ''),
        ('Elisabeth Reynolds', 'Affiliated Researcher; Principal Research Scientist', '', ''),
        ('Katharine Donato', 'Affiliated Faculty; Professor of Sociology', '', ''),
        ('Roberto Fernandez', 'Affiliated Faculty; Professor, Sloan School of Management', '', ''),
        ('Ray Reagans', 'Affiliated Faculty; Professor, Sloan School of Management', '', ''),
        ('Zeynep Ton', 'Affiliated Faculty; Professor of Management, Sloan', '', ''),
        ('Thomas Kochan', 'Affiliated Faculty; George Maverick Bunker Professor of Management', '', ''),
        ('Emilio Castilla', 'Affiliated Faculty; Professor of Management, Sloan', '', ''),
        ('David Mindell', 'Affiliated Faculty; Frances and David Dibner Professor of the History of Engineering and Manufacturing', '', ''),
    ],
    'sfi-epe': [
        ('David Krakauer', 'President, Santa Fe Institute', '', ''),
        ('Jenna Bednar', 'Affiliated Researcher; Professor of Political Science, University of Michigan', '', ''),
        ('Tyler Marghetis', 'Affiliated Researcher', '', ''),
        ('Simon DeDeo', 'Affiliated Researcher; Assistant Professor, Carnegie Mellon University', '', ''),
        ('Elizabeth Bruch', 'Affiliated Researcher; Associate Professor, University of Michigan', '', ''),
        ('Cristina Bicchieri', 'Affiliated Researcher; Professor of Philosophy and Psychology, UPenn', '', ''),
        ('Eric Beinhocker', 'Affiliated Researcher; Director, INET Oxford', '', ''),
    ],
    'besi-berkeley': [
        ('Paul Pierson', 'Director; John Gross Professor of Political Science', '', ''),
        ('Jonas Meckling', 'Climate Research Lead; Professor of Political Science', '', ''),
        ('Marion Fourcade', 'Technology Research Lead; Professor of Sociology', '', ''),
        ('Cecilia Ridgeway', 'Affiliated Faculty; Emeritus Professor of Sociology', '', ''),
        ('Sanford Jacoby', 'Affiliated Faculty; Professor, UCLA Anderson School', '', ''),
        ('J. Bradford DeLong', 'Affiliated Faculty; Professor of Economics', '', ''),
        ('Robert Reich', 'Affiliated Faculty; Professor of Public Policy', '', ''),
        ('Henry Brady', 'Affiliated Faculty; Professor of Political Science and Public Policy', '', ''),
        ('Laura Tyson', 'Affiliated Faculty; Professor of Economics, Haas School', '', ''),
        ('David Vogel', 'Affiliated Faculty; Emeritus Professor of Political Science and Business', '', ''),
        ('Cathie Jo Martin', 'Affiliated Faculty; Professor of Political Science, Boston University', '', ''),
        ('Peter Evans', 'Affiliated Faculty; Emeritus Professor of Sociology', '', ''),
        ('Steven Vogel', 'Affiliated Faculty; Il Han New Professor of Asian Studies', '', ''),
        ('Kim Voss', 'Affiliated Faculty; Professor of Sociology', '', ''),
        ('Evan Mast', 'Affiliated Researcher; Research Economist', '', ''),
        ('Eric Biber', 'Affiliated Faculty; Professor of Law', '', ''),
    ],
}


def slugify(name):
    name = unicodedata.normalize('NFKD', name).encode('ascii', 'ignore').decode()
    name = re.sub(r'[^\w\s-]', '', name.lower())
    return re.sub(r'[\s_]+', '-', name).strip('-')


def make_individual(center_id, name, title, email, website):
    ctr = CENTERS[center_id]
    return {
        'id':             slugify(name),
        'name':           name,
        'title':          title,
        'center_id':      center_id,
        'center_name':    ctr['name'],
        'institution':    ctr['institution'],
        'country':        ctr['country'],
        'region':         ctr['region'],
        'email':          email,
        'website':        website,
        'topics_current':    [],
        'topics_anticipated':[],
        'topics_would_like': [],
        'teaching_regions':  [],
        'teaching_levels':   [],
        'connected_networks':[],
        'problems':       '',
        'opportunities':  '',
        'notes':          '',
        'updated':        TODAY,
    }


def main():
    # Load existing individuals (preserve any with real topic data from form responses)
    existing = {}
    if OUT.exists():
        for ind in json.loads(OUT.read_text()):
            existing[ind['id']] = ind

    individuals = []
    seen_ids = set()

    for center_id, people in PEOPLE.items():
        for (name, title, email, website) in people:
            uid = slugify(name)
            if uid in seen_ids:
                continue
            seen_ids.add(uid)
            if uid in existing and (
                existing[uid].get('topics_current') or
                existing[uid].get('topics_anticipated') or
                existing[uid].get('email')
            ):
                # Preserve richer existing record but update center linkage
                rec = dict(existing[uid])
                rec['center_id']   = center_id
                rec['center_name'] = CENTERS[center_id]['name']
                individuals.append(rec)
            else:
                individuals.append(make_individual(center_id, name, title, email, website))

    individuals.sort(key=lambda x: (x['center_id'], x['name']))
    OUT.write_text(json.dumps(individuals, indent=2, ensure_ascii=False) + '\n')

    by_center = {}
    for ind in individuals:
        by_center.setdefault(ind['center_id'], 0)
        by_center[ind['center_id']] += 1
    print(f'Wrote {len(individuals)} individuals to {OUT}')
    for cid, count in sorted(by_center.items()):
        print(f'  {cid}: {count}')


if __name__ == '__main__':
    main()
