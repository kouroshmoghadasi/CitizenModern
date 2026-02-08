# -*- coding: utf-8 -*-
"""Add French (summary-item-fr) for any summary-item-en that doesn't have it."""
import re
import os

HTML_PATH = os.path.join(os.path.dirname(__file__), '..', 'templates', 'book_summary.html')

# English -> French for remaining items (order doesn't matter; we replace by exact EN text)
EN_FR = {
    "NAFTA (North American Free Trade Agreement) - Between Canada, USA, and Mexico (1994)": "ALENA – Entre le Canada, les États-Unis et le Mexique (1994)",
    "USMCA/CUSMA (New North American Free Trade Agreement) - Replaced NAFTA in 2020": "ACEUM – A remplacé l'ALENA en 2020",
    "CETA (Comprehensive Economic and Trade Agreement) - Between Canada and European Union": "AECG – Entre le Canada et l'Union européenne",
    "CPTPP (Comprehensive and Progressive Agreement for Trans-Pacific Partnership) - Includes 11 countries": "PTPGP – Inclut 11 pays",
    "Canada is a member of the United Nations (UN)": "Le Canada est membre de l'Organisation des Nations Unies (ONU)",
    "Canada is a member of NATO (North Atlantic Treaty Organization)": "Le Canada est membre de l'OTAN",
    "Canada is a member of G7 (Group of Seven) - Advanced industrial countries": "Le Canada est membre du G7 – Pays industriels avancés",
    "Canada is a member of G20 (Group of Twenty) - World's largest economies": "Le Canada est membre du G20 – Plus grandes économies mondiales",
    "Canada is a member of the Commonwealth": "Le Canada est membre du Commonwealth",
    "Canada is a member of La Francophonie": "Le Canada est membre de la Francophonie",
    "Treaty of Paris (1763) - End of Seven Years' War and cession of New France to Britain": "Traité de Paris (1763) – Fin de la guerre de Sept Ans et cession de la Nouvelle-France à la Grande-Bretagne",
    "British North America Act (1867) - Creation of Canadian Confederation": "Acte de l'Amérique du Nord britannique (1867) – Création de la Confédération canadienne",
    "Canada Act (1982) - Full constitutional independence from Britain": "Loi sur le Canada (1982) – Indépendance constitutionnelle complète de la Grande-Bretagne",
    "Treaties with Aboriginal peoples - Over 70 treaties between Canadian government and First Nations": "Traités avec les Autochtones – Plus de 70 traités entre le gouvernement et les Premières Nations",
    "49th Parallel - Border between Canada and USA from ocean to Great Lakes": "49e parallèle – Frontière entre le Canada et les États-Unis",
    "Oregon Treaty (1846) - Established border in the west": "Traité de l'Oregon (1846) – Établissement de la frontière à l'ouest",
    "Treaty of Ghent (1814) - Established border in the east": "Traité de Gand (1814) – Établissement de la frontière à l'est",
    "British North America Act (1867) - Original constitution that created Confederation": "Acte de l'Amérique du Nord britannique (1867) – Constitution originale ayant créé la Confédération",
    "Constitution Act 1982 - Includes Charter of Rights and Freedoms": "Loi constitutionnelle de 1982 – Inclut la Charte des droits et libertés",
    "Canada Act 1982 - Full constitutional independence": "Loi sur le Canada de 1982 – Indépendance constitutionnelle complète",
    "Multiculturalism Act (1988) - Recognition of cultural diversity": "Loi sur le multiculturalisme (1988) – Reconnaissance de la diversité culturelle",
    "Official Languages Act (1969) - Guarantees use of English and French": "Loi sur les langues officielles (1969) – Garantit l'usage de l'anglais et du français",
    "Supreme Court of Canada - Highest court in Canada": "Cour suprême du Canada – Plus haute cour du Canada",
    "Bank of Canada - Responsible for monetary policy": "Banque du Canada – Responsable de la politique monétaire",
    "RCMP (Royal Canadian Mounted Police) - Federal police": "GRC (Gendarmerie royale du Canada) – Police fédérale",
    "CBC (Canadian Broadcasting Corporation) - National broadcaster": "SRC (Société Radio-Canada) – Radiodiffuseur national",
    "Rebellions of 1837 - Uprisings in Upper and Lower Canada": "Rébellions de 1837 – Soulèvements au Haut et au Bas-Canada",
    "Charlottetown Conference (1864) - First Confederation conference": "Conférence de Charlottetown (1864) – Première conférence sur la Confédération",
    "Quebec Conference (1864) - Drafting Confederation principles": "Conférence de Québec (1864) – Rédaction des principes de la Confédération",
    "Winnipeg General Strike (1919) - Largest strike in Canadian history": "Grève générale de Winnipeg (1919) – Plus grande grève de l'histoire du Canada",
    "October Crisis (1970) - Terrorist crisis in Quebec": "Crise d'octobre (1970) – Crise terroriste au Québec",
    "Quebec Referendums (1980, 1995) - Quebec independence referendums": "Référendums au Québec (1980, 1995) – Référendums sur l'indépendance",
    "Alexander Graham Bell - Invention of telephone (though patented in USA)": "Alexander Graham Bell – Invention du téléphone",
    "Frederick Banting and Charles Best - Discovery of insulin (1921)": "Frederick Banting et Charles Best – Découverte de l'insuline (1921)",
    "Armstrong Whitworth - Invention of guided missile": "Armstrong Whitworth – Invention du missile guidé",
    "Canadarm - Robotic arm for space shuttle": "Canadarm – Bras robotique pour la navette spatiale",
    "17 UNESCO World Heritage Sites in Canada": "17 sites du patrimoine mondial de l'UNESCO au Canada",
    "National Historic Sites - Over 1000 registered sites": "Lieux historiques nationaux – Plus de 1000 sites enregistrés",
    "National museums: Canadian Museum of History, Museum of Civilization, National Gallery": "Musées nationaux : Musée canadien de l'histoire, Musée des civilisations, Galerie nationale",
    "Ontario: Most populous province, home to Canada's capital (Ottawa) and largest city (Toronto)": "Ontario : Province la plus peuplée, capitale (Ottawa) et plus grande ville (Toronto)",
    "Quebec: Only province with French as official language, second most populous province": "Québec : Seule province avec le français comme langue officielle",
    "British Columbia: On Pacific coast, known for mountains and nature": "Colombie-Britannique : Côte du Pacifique, montagnes et nature",
    "Alberta: Known for oil and gas industry, Rocky Mountains": "Alberta : Industrie pétrolière et gazière, Rocheuses",
    "Saskatchewan: \"Breadbasket of Canada\", largest wheat producer": "Saskatchewan : « Grenier du Canada », plus grand producteur de blé",
    "Manitoba: \"Province of a Thousand Lakes\", geographic center of Canada": "Manitoba : « Province des mille lacs », centre géographique du Canada",
    "Nova Scotia: \"Ocean Playground of Canada\", known for fishing industry": "Nouvelle-Écosse : « Terrain de jeu océanique du Canada », industrie de la pêche",
    "New Brunswick: Only officially bilingual province (English and French)": "Nouveau-Brunswick : Seule province officiellement bilingue",
    "Prince Edward Island: Smallest province, known for potatoes and Anne of Green Gables": "Île-du-Prince-Édouard : Plus petite province, pommes de terre et Anne aux pignons verts",
    "Newfoundland and Labrador: Youngest province (1949), known for culture and fishing": "Terre-Neuve-et-Labrador : Plus jeune province (1949), culture et pêche",
    "Yukon: Smallest and westernmost territory, known for Klondike Gold Rush": "Yukon : Plus petit et plus à l'ouest, ruée vers l'or du Klondike",
    "Northwest Territories: Largest territory, has diamonds and gold": "Territoires du Nord-Ouest : Plus grand territoire, diamants et or",
    "Nunavut: Youngest and largest territory (1999), majority Inuit population": "Nunavut : Plus jeune et plus grand territoire (1999), majorité inuite",
    "1534: Jacques Cartier arrived in Canada": "1534 : Jacques Cartier arrive au Canada",
    "1608: Samuel de Champlain founded Quebec City": "1608 : Samuel de Champlain fonde Québec",
    "1763: Treaty of Paris - New France ceded to Britain": "1763 : Traité de Paris – Nouvelle-France cédée à la Grande-Bretagne",
    "1867: Canadian Confederation - July 1 (Canada Day)": "1867 : Confédération canadienne – 1er juillet (Fête du Canada)",
    "1914-1918: World War I": "1914-1918 : Première Guerre mondiale",
    "1917: Battle of Vimy Ridge": "1917 : Bataille de la crête de Vimy",
    "1939-1945: World War II": "1939-1945 : Deuxième Guerre mondiale",
    "1965: Canada's maple leaf flag adopted": "1965 : Adoption du drapeau canadien à la feuille d'érable",
    "1982: Canada's Constitution - Full independence": "1982 : Constitution du Canada – Indépendance complète",
    "10 provinces and 3 territories": "10 provinces et 3 territoires",
    "338 members in House of Commons": "338 députés à la Chambre des communes",
    "105 senators in Senate": "105 sénateurs au Sénat",
    "18 years: Minimum age to vote": "18 ans : Âge minimum pour voter",
    "At least every 5 years: Federal elections must be held": "Au moins tous les 5 ans : Élections fédérales obligatoires",
    "2 official languages: English and French": "2 langues officielles : anglais et français",
    "2 national sports: Hockey (winter), Lacrosse (summer)": "2 sports nationaux : hockey (hiver), crosse (été)",
    "4 original Confederation provinces: Ontario, Quebec, Nova Scotia, New Brunswick": "4 provinces fondatrices : Ontario, Québec, Nouvelle-Écosse, Nouveau-Brunswick",
    "5 Great Lakes: Superior, Huron, Michigan, Erie, Ontario": "5 Grands Lacs : Supérieur, Huron, Michigan, Érié, Ontario",
    "Parliamentary Democracy: System of government where Parliament is the primary legislative body": "Démocratie parlementaire : Le Parlement est l'organe législatif principal",
    "Constitutional Monarchy: King/Queen is head of state but power is limited": "Monarchie constitutionnelle : Le roi/la reine est chef d'État mais le pouvoir est limité",
    "Federalism: Division of power between federal and provincial governments": "Fédéralisme : Partage des pouvoirs entre le fédéral et les provinces",
    "Responsible Government: Government must be accountable to Parliament": "Gouvernement responsable : Le gouvernement est responsable devant le Parlement",
    "Collective Rights: Rights of groups such as Aboriginal peoples": "Droits collectifs : Droits des groupes comme les Autochtones",
    "Individual Rights: Rights of each person as an individual": "Droits individuels : Droits de chaque personne",
    "Common Law: Legal system based on judicial precedent (in all provinces except Quebec)": "Common law : Système juridique fondé sur la jurisprudence (sauf au Québec)",
    "Civil Law: Legal system based on written laws (in Quebec)": "Droit civil : Système fondé sur les lois écrites (au Québec)",
    "Jury: Group of citizens who make decisions in court": "Jury : Groupe de citoyens qui prennent des décisions en cour",
    "Jury Duty: A legal duty of citizenship": "Devoir de juré : Obligation légale du citoyen",
    "Multiculturalism: Recognition and respect for different cultures": "Multiculturalisme : Reconnaissance et respect des cultures",
    "Bilingualism: Use of two languages (English and French)": "Bilinguisme : Usage de deux langues (anglais et français)",
    "Cultural Diversity: Existence of different cultures and ethnicities in a society": "Diversité culturelle : Présence de différentes cultures et ethnies",
    "Equality: All individuals have equal rights and opportunities": "Égalité : Tous ont des droits et des chances égaux",
    "The test consists of 20 questions": "L'examen comprend 20 questions",
    "To pass, you must answer at least 15 questions correctly (75%)": "Pour réussir, il faut au moins 15 bonnes réponses (75 %)",
    "Test duration: 45 minutes": "Durée de l'examen : 45 minutes",
    "Questions are based on the \"Discover Canada\" book": "Les questions sont basées sur le guide « Découvrir le Canada »",
    "The test is conducted in English or French": "L'examen se fait en anglais ou en français",
    "People over 54 and under 18 are exempt from the test": "Les personnes de plus de 54 ans et de moins de 18 ans sont exemptées",
}

def main():
    with open(HTML_PATH, 'r', encoding='utf-8') as f:
        content = f.read()

    for en, fr in EN_FR.items():
        old = '<div class="summary-item-en">' + en + '</div>\n                        </li>'
        new = '<div class="summary-item-en">' + en + '</div>\n                            <div class="summary-item-fr">' + fr + '</div>\n                        </li>'
        if old in content:
            content = content.replace(old, new, 1)
        else:
            # Try with different whitespace
            old2 = '<div class="summary-item-en">' + re.escape(en) + '</div>'
            if re.search(old2, content):
                content = re.sub(
                    r'(<div class="summary-item-en">' + re.escape(en) + r'</div>)\s*\n(\s*)</li>',
                    r'\1\n                            <div class="summary-item-fr">' + fr + r'</div>\n\2</li>',
                    content,
                    count=1
                )

    with open(HTML_PATH, 'w', encoding='utf-8') as f:
        f.write(content)
    print('Done. Added FR for', len(EN_FR), 'items.')

if __name__ == '__main__':
    main()
