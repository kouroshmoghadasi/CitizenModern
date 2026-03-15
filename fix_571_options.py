# Fix 571 questions with <4 options. Run once then delete.
import json
path = 'static/citizenship_571_questions.json'
with open(path, 'r', encoding='utf-8') as f:
    data = json.load(f)

def fix(q, opts_en, opts_fr, book_text='', expl_fr='', q_en=None):
    if q_en:
        q['q'] = q_en
    q['options'] = opts_en
    q['options_fr'] = opts_fr
    if book_text:
        q['book_text'] = book_text
    if expl_fr:
        q['expl_fr'] = expl_fr

fixed = 0
# Q3 (index 2): BNA Act
if data[2]['q'].startswith('When did the British North America') and len(data[2]['options']) == 1:
    fix(data[2], ['1867', '1763', '1791', '1982'], ['1867', '1763', '1791', '1982'],
        'The British North America Act came into effect in 1867.',
        "L'Acte de l'Amérique du Nord britannique est entré en vigueur en 1867.")
    fixed += 1; print('Fixed Q3')

# Q13 (index 12): Plains of Abraham
if 'Plains of Abraham' in data[12]['q'] and data[12].get('options') == ['(Multiple choice)']:
    fix(data[12],
        ["The British defeated the French, marking the end of France's empire in America", "The French defeated the British", "American forces captured Quebec", "The war ended in a truce"],
        ["Les Britanniques ont vaincu les Français, marquant la fin de l'empire français en Amérique", "Les Français ont vaincu les Britanniques", "Les forces américaines ont capturé Québec", "La guerre s'est terminée par une trêve"],
        "The British defeated the French, marking the end of France's empire in America.",
        "Les Britanniques ont vaincu les Français, marquant la fin de l'empire français en Amérique.",
        "What happened at the Battle of the Plains of Abraham?")
    fixed += 1; print('Fixed Q13')

# Q15 (index 14): English and French equal status
if 'English and French have equal status' in data[14]['q'] and len(data[14]['options']) == 1:
    fix(data[14], ['In the Parliament of Canada', 'Only in Quebec schools', 'Only in federal courts', 'Only in New Brunswick'],
        ['Au Parlement du Canada', 'Uniquement dans les écoles du Québec', 'Uniquement dans les tribunaux fédéraux', 'Uniquement au Nouveau-Brunswick'],
        'English and French have equal status in the Parliament of Canada and in federal institutions.')
    fixed += 1; print('Fixed Q15')

# Q16 (index 15): presumption of innocence
if 'presumption of innocence' in data[15]['q'] and len(data[15]['options']) == 1:
    fix(data[15], ['Everyone is innocent until proven guilty', 'The accused must prove their innocence', 'Only judges decide guilt', 'Police can decide guilt'],
        ['Tout le monde est innocent jusqu\'à preuve du contraire', 'L\'accusé doit prouver son innocence', 'Seuls les juges décident de la culpabilité', 'La police peut décider de la culpabilité'],
        'Everyone is innocent until proven guilty.')
    fixed += 1; print('Fixed Q16')

# Q17 (index 16): only officially bilingual province
if 'only officially bilingual' in data[16]['q'] and len(data[16]['options']) == 1:
    fix(data[16], ['New Brunswick', 'Quebec', 'Ontario', 'Manitoba'],
        ['Nouveau-Brunswick', 'Québec', 'Ontario', 'Manitoba'])
    fixed += 1; print('Fixed Q17')

# Q18 (index 17): Canadian flag
if 'Canadian flag look like' in data[17]['q'] and data[17].get('options') == ['(Multiple choice)']:
    fix(data[17],
        ['White with red borders and a red maple leaf in the center', 'Blue with a Union Jack', 'Red and white with a fleur-de-lis', 'Green with a maple leaf'],
        ['Blanc avec des bordures rouges et une feuille d\'érable rouge au centre', 'Bleu avec un Union Jack', 'Rouge et blanc avec une fleur de lys', 'Vert avec une feuille d\'érable'],
        q_en='What does the Canadian flag look like?')
    fixed += 1; print('Fixed Q18')

# Q19 (index 18): national anthem
if 'national anthem' in data[18]['q'] and 'What song' in data[18]['q'] and len(data[18]['options']) == 1:
    fix(data[18], ['O Canada', 'God Save the Queen', 'The Maple Leaf Forever', 'Alouette'],
        ['Ô Canada', 'God Save the Queen', 'The Maple Leaf Forever', 'Alouette'])
    fixed += 1; print('Fixed Q19')

# Q20 (index 19): first two lines of anthem
if 'first two lines' in data[19]['q'] and data[19].get('options') == ['(Multiple choice)']:
    fix(data[19],
        ['O Canada! Our home and native land!', 'God save our gracious Queen', 'From far and wide, O Canada', 'The True North strong and free'],
        ['Ô Canada! Notre maison et notre terre natale!', 'God save our gracious Queen', 'D\'un océan à l\'autre', 'The True North strong and free'],
        q_en='Give the first two lines of Canada\'s national anthem.')
    fixed += 1; print('Fixed Q20')

# Q21 (index 20): name Canada from
if 'name' in data[20]['q'] and 'Canada' in data[20]['q'] and data[20].get('options') == ['(Multiple choice)']:
    fix(data[20],
        ['From "Kanata", the Huron-Iroquois word for village', 'From the Latin word for north', 'From a French explorer\'s name', 'From the British Crown'],
        ['De « Kanata », mot huron-iroquois signifiant village', 'Du mot latin pour nord', 'Du nom d\'un explorateur français', 'De la Couronne britannique'],
        q_en='From where does the name Canada come?')
    fixed += 1; print('Fixed Q21')

# Q22 (index 21): official symbol animal
if 'official symbol' in data[21]['q'] and 'Canada' in data[21]['q'] and len(data[21]['options']) == 1:
    fix(data[21], ['The beaver', 'The moose', 'The bear', 'The loon'],
        ['Le castor', 'L\'orignal', 'L\'ours', 'Le huard'])
    fixed += 1; print('Fixed Q22')

# Q23 (index 22): population
if 'population of Canada' in data[22]['q'] and len(data[22]['options']) == 1:
    fix(data[22], ['About 34 million', 'About 50 million', 'About 20 million', 'About 40 million'],
        ['Environ 34 millions', 'Environ 50 millions', 'Environ 20 millions', 'Environ 40 millions'])
    fixed += 1; print('Fixed Q23')

# Q24 (index 23): three oceans
if 'three oceans' in data[23]['q'] and len(data[23]['options']) == 1:
    fix(data[23], ['Atlantic, Arctic and Pacific', 'Atlantic, Indian and Pacific', 'Arctic, Indian and Pacific', 'Atlantic, Pacific and Southern'],
        ['Atlantique, Arctique et Pacifique', 'Atlantique, Indien et Pacifique', 'Arctique, Indien et Pacifique', 'Atlantique, Pacifique et Austral'])
    fixed += 1; print('Fixed Q24')

# Q25 (index 24): Central Canada provinces and capitals
if 'Central Canada' in data[24]['q'] and len(data[24]['options']) == 1:
    fix(data[24], ['Ontario (Toronto) and Quebec (Quebec City)', 'Manitoba (Winnipeg) and Saskatchewan (Regina)', 'Nova Scotia (Halifax) and New Brunswick (Fredericton)', 'Alberta (Edmonton) and BC (Victoria)'],
        ['Ontario (Toronto) et Québec (Québec)', 'Manitoba (Winnipeg) et Saskatchewan (Regina)', 'Nouvelle-Écosse (Halifax) et Nouveau-Brunswick (Fredericton)', 'Alberta (Edmonton) et C.-B. (Victoria)'])
    fixed += 1; print('Fixed Q25')

# Q26 (index 25): Quebecers
if 'Quebecers' in data[25]['q'] and len(data[25]['options']) == 1:
    fix(data[25], ['People of Quebec', 'People of French descent only', 'First Nations of Quebec', 'Inuit of the North'],
        ['Les gens du Québec', 'Les personnes d\'origine française uniquement', 'Les Premières Nations du Québec', 'Les Inuits du Nord'])
    fixed += 1; print('Fixed Q26')

# Q27 (index 26): Acadians
if 'Acadians' in data[26]['q'] and len(data[26]['options']) == 1:
    fix(data[26], ['Descendants of French colonists who settled in the Maritime provinces in 1604', 'British settlers in Nova Scotia', 'Indigenous people of the East', 'Loyalists who left the USA'],
        ['Descendants des colons français établis dans les provinces maritimes en 1604', 'Colons britanniques en Nouvelle-Écosse', 'Peuples autochtones de l\'Est', 'Loyalistes qui ont quitté les États-Unis'])
    fixed += 1; print('Fixed Q27')

# Q28 (index 27): largest religious affiliation
if 'largest religious affiliation' in data[27]['q'] and len(data[27]['options']) == 1:
    fix(data[27], ['Catholic', 'Protestant', 'Muslim', 'No religion'],
        ['Catholique', 'Protestant', 'Musulman', 'Sans religion'])
    fixed += 1; print('Fixed Q28')

# Q29 (index 28): Constitutional Act 1791
if 'legislative assemblies' in data[28]['q'] and len(data[28]['options']) == 1:
    fix(data[28], ['The Constitutional Act of 1791', 'The British North America Act', 'The Quebec Act', 'The Royal Proclamation'],
        ['L\'Acte constitutionnel de 1791', 'L\'Acte de l\'Amérique du Nord britannique', 'L\'Acte de Québec', 'La Proclamation royale'])
    fixed += 1; print('Fixed Q29')

# Q30 (index 29): first leader responsible government
if 'first leader of a responsible government' in data[29]['q'] and len(data[29]['options']) == 1:
    fix(data[29], ['Sir Louis-Hippolyte La Fontaine', 'Sir John A. Macdonald', 'William Lyon Mackenzie King', 'Sir Robert Borden'],
        ['Sir Louis-Hippolyte La Fontaine', 'Sir John A. Macdonald', 'William Lyon Mackenzie King', 'Sir Robert Borden'])
    fixed += 1; print('Fixed Q30')

# Q31 (index 30): Sir Sam Steele
if 'Sir Sam Steele' in data[30]['q'] and data[30].get('options') == ['(Multiple choice)']:
    fix(data[30], ['A great frontier hero, Mounted Policeman and soldier of the Queen', 'The first Prime Minister', 'A Father of Confederation', 'An explorer of the Arctic'],
        ['Un grand héros des frontières, policier à cheval et soldat de la Reine', 'Le premier premier ministre', 'Un Père de la Confédération', 'Un explorateur de l\'Arctique'],
        q_en='Who was Sir Sam Steele?')
    fixed += 1; print('Fixed Q31')

# Q32 (index 31): CPR / Chinese railroad
if 'Canadian Pacific Railway' in data[31]['q'] and len(data[31]['options']) == 1:
    fix(data[31], ['Chinese railroad workers', 'British engineers only', 'American investors', 'First Nations guides only'],
        ['Les travailleurs chinois du chemin de fer', 'Les ingénieurs britanniques uniquement', 'Les investisseurs américains', 'Les guides des Premières Nations uniquement'])
    fixed += 1; print('Fixed Q32')

# Q33 (index 32): head tax
if 'head tax' in data[32]['q'] and data[32].get('options') == ['(Multiple choice)']:
    fix(data[32], ['A race-based entry fee charged for Chinese entering Canada', 'A tax on income', 'A fee for citizenship', 'A provincial sales tax'],
        ['Frais d\'entrée basés sur la race imposés aux Chinois entrant au Canada', 'Un impôt sur le revenu', 'Des frais pour la citoyenneté', 'Une taxe de vente provinciale'],
        q_en='What was the "head tax"?')
    fixed += 1; print('Fixed Q33')

# Q34 (index 33): General Sir Arthur Currie
if 'General Sir Arthur Currie' in data[33]['q'] and len(data[33]['options']) == 1:
    fix(data[33], ['Canada\'s greatest soldier in the First World War', 'A Father of Confederation', 'The first Governor General', 'A Prime Minister'],
        ['Le plus grand soldat canadien de la Première Guerre mondiale', 'Un Père de la Confédération', 'Le premier gouverneur général', 'Un premier ministre'])
    fixed += 1; print('Fixed Q34')

# Q35 (index 34): Remembrance Day
if 'Remembrance Day celebrated' in data[34]['q'] and len(data[34]['options']) == 1:
    fix(data[34], ['November 11th', 'July 1st', 'December 25th', 'June 6th'],
        ['Le 11 novembre', 'Le 1er juillet', 'Le 25 décembre', 'Le 6 juin'])
    fixed += 1; print('Fixed Q35')

# Q36 (index 35): CPR symbolize
if 'Canadian Pacific Railway symbolize' in data[35]['q'] and len(data[35]['options']) == 1:
    fix(data[35], ['Unity', 'Trade', 'Independence', 'Wealth'],
        ['Unité', 'Commerce', 'Indépendance', 'Richesse'])
    fixed += 1; print('Fixed Q36')
# Q37 (index 36): highest military honor
if 'highest military honor' in data[36]['q'] and len(data[36]['options']) == 1:
    fix(data[36], ['Victoria Cross', 'Order of Canada', 'Medal of Bravery', 'Star of Courage'],
        ['Croix de Victoria', 'Ordre du Canada', 'Médaille de la bravoure', 'Étoile du courage'])
    fixed += 1; print('Fixed Q37')
# Q38 (index 37): Vimy Ridge
if 'Vimy Ridge' in data[37]['q'] and data[37].get('options') == ['(Multiple choice)']:
    fix(data[37], ['Canadian Corps secured its reputation for valour and bravery', 'Canada became independent', 'The war ended', 'Americans joined the war'],
        ['Le Corps canadien a assuré sa réputation de vaillance et de bravoure', 'Le Canada est devenu indépendant', 'La guerre s\'est terminée', 'Les Américains sont entrés en guerre'],
        q_en='Why is the battle of Vimy Ridge important?')
    fixed += 1; print('Fixed Q38')
# Q39 (index 38): 3 territories and how many provinces
if '3 territories' in data[38]['q'] and len(data[38]['options']) == 1:
    fix(data[38], ['10', '13', '8', '12'],
        ['10', '13', '8', '12'])
    fixed += 1; print('Fixed Q39')
# Q40 (index 39): 2 responsibilities provincial/territorial
if 'provincial and territorial' in data[39]['q'] and len(data[39]['options']) == 1:
    fix(data[39], ['Health and Education', 'National defence and Foreign policy', 'Currency and Citizenship', 'Criminal law'],
        ['Santé et éducation', 'Défense nationale et politique étrangère', 'Monnaie et citoyenneté', 'Droit criminel'])
    fixed += 1; print('Fixed Q40')
# Q41 (index 40): Head of Government
if 'Head of Government' in data[40]['q'] and len(data[40]['options']) == 1:
    fix(data[40], ['The Prime Minister', 'The Queen', 'The Governor General', 'The Premier'],
        ['Le Premier ministre', 'La Reine', 'Le gouverneur général', 'Le premier ministre provincial'])
    fixed += 1; print('Fixed Q41')
# Q42 (index 41): highest court
if 'highest court in Canada' in data[41]['q'] and len(data[41]['options']) == 1:
    fix(data[41], ['The Supreme Court of Canada', 'The Federal Court', 'The Provincial Court', 'The Court of Appeal'],
        ['La Cour suprême du Canada', 'La Cour fédérale', 'La Cour provinciale', 'La Cour d\'appel'])
    fixed += 1; print('Fixed Q42')
# Q43 (index 42): first province voting rights women
if 'voting rights to women' in data[42]['q'] and len(data[42]['options']) == 1:
    fix(data[42], ['Manitoba', 'Ontario', 'Quebec', 'British Columbia'],
        ['Manitoba', 'Ontario', 'Québec', 'Colombie-Britannique'])
    fixed += 1; print('Fixed Q43')
# Q44 (index 43): Newfoundland join Canada year
if 'Newfoundland and Labrador join' in data[43]['q'] and len(data[43]['options']) == 1:
    fix(data[43], ['1949', '1867', '1905', '1945'],
        ['1949', '1867', '1905', '1945'])
    fixed += 1; print('Fixed Q44')
# Q45 (index 44): provincial flag fleur-de-lys
if 'fleur-de' in data[44]['q'] and len(data[44]['options']) == 1:
    fix(data[44], ['Quebec', 'New Brunswick', 'Ontario', 'Manitoba'],
        ['Québec', 'Nouveau-Brunswick', 'Ontario', 'Manitoba'],
        q_en='Which provincial flag features the fleur-de-lys?')
    fixed += 1; print('Fixed Q45')
# Q46 (index 45): Canada rank largest countries
if 'rank' in data[45]['q'] and 'largest countries' in data[45]['q'] and len(data[45]['options']) == 1:
    fix(data[45], ['Second', 'First', 'Third', 'Fourth'],
        ['Deuxième', 'Premier', 'Troisième', 'Quatrième'])
    fixed += 1; print('Fixed Q46')
# Q47 (index 46): province own time zone
if 'own time zone' in data[46]['q'] and len(data[46]['options']) == 1:
    fix(data[46], ['Newfoundland and Labrador', 'Quebec', 'Saskatchewan', 'British Columbia'],
        ['Terre-Neuve-et-Labrador', 'Québec', 'Saskatchewan', 'Colombie-Britannique'])
    fixed += 1; print('Fixed Q47')
# Q48 (index 47): largest busiest port
if 'largest and busiest' in data[47]['q'] and 'port' in data[47]['q'] and len(data[47]['options']) == 1:
    fix(data[47], ['The Port of Vancouver', 'The Port of Montreal', 'The Port of Halifax', 'The Port of Saint John'],
        ['Le port de Vancouver', 'Le port de Montréal', 'Le port de Halifax', 'Le port de Saint-Jean'])
    fixed += 1; print('Fixed Q48')
# Q49 (index 48): party in power Ontario - note: can change over time, Liberal was correct at source
if 'political party' in data[48]['q'] and 'Ontario' in data[48]['q'] and len(data[48]['options']) == 1:
    fix(data[48], ['Liberal Party', 'Conservative Party', 'NDP', 'Green Party'],
        ['Parti libéral', 'Parti conservateur', 'NPD', 'Parti vert'])
    fixed += 1; print('Fixed Q49')
# Q50 (index 49): secret ballot
if 'secret ballot' in data[49]['q'] and data[49].get('options') == ['(Multiple choice)']:
    fix(data[49], ['No one can watch your vote, and no one should look at how you voted', 'You must tell your employer how you voted', 'Only the party leader can see your vote', 'Your vote is public record'],
        ['Personne ne peut surveiller votre vote, et personne ne doit regarder comment vous avez voté', 'Vous devez dire à votre employeur comment vous avez voté', 'Seul le chef du parti peut voir votre vote', 'Votre vote est un document public'],
        q_en='What does the right to a secret ballot mean?')
    fixed += 1; print('Fixed Q50')
# Q51 (index 50): Head of State
if 'Head of State' in data[50]['q'] and len(data[50]['options']) == 1:
    fix(data[50], ['Her Majesty the Queen (or King)', 'The Prime Minister', 'The Governor General', 'The President'],
        ['Sa Majesté la Reine (ou le Roi)', 'Le Premier ministre', 'Le gouverneur général', 'Le président'])
    fixed += 1; print('Fixed Q51')
# Q52 (index 51): Queen's representative
if 'representative' in data[51]['q'] and 'Queen' in data[51]['q'] and 'Canada' in data[51]['q'] and len(data[51]['options']) == 1:
    fix(data[51], ['The Governor General of Canada', 'The Prime Minister', 'The Lieutenant Governor', 'The Premier'],
        ['Le gouverneur général du Canada', 'Le Premier ministre', 'Le lieutenant-gouverneur', 'Le premier ministre provincial'])
    fixed += 1; print('Fixed Q52')
# Q53 (index 52): Sovereign's representative in provinces
if 'representative' in data[52]['q'] and 'provinces' in data[52]['q'] and len(data[52]['options']) == 1:
    fix(data[52], ['Lieutenant-Governor', 'Governor General', 'Premier', 'Mayor'],
        ['Lieutenant-gouverneur', 'Gouverneur général', 'Premier ministre provincial', 'Maire'])
    fixed += 1; print('Fixed Q53')
# Q54 (index 53): system of government
if "system of government" in data[53]['q'] and len(data[53]['options']) == 1:
    fix(data[53], ['Parliamentary government', 'Presidential government', 'Direct democracy', 'Constitutional monarchy only'],
        ['Gouvernement parlementaire', 'Gouvernement présidentiel', 'Démocratie directe', 'Monarchie constitutionnelle uniquement'])
    fixed += 1; print('Fixed Q54')
# Q55 (index 54): three parts of Parliament
if 'three parts of Parliament' in data[54]['q'] and len(data[54]['options']) == 1:
    fix(data[54], ['The Queen, the House of Commons and the Senate', 'The Prime Minister, the Cabinet and the Opposition', 'Federal, Provincial and Municipal', 'The Legislature, the Executive and the Judiciary'],
        ['La Reine, la Chambre des communes et le Sénat', 'Le Premier ministre, le Cabinet et l\'Opposition', 'Fédéral, provincial et municipal', 'Le législatif, l\'exécutif et le judiciaire'])
    fixed += 1; print('Fixed Q55')
# Q56 (index 55): law before it is passed
if 'law before it is passed' in data[55]['q'] and len(data[55]['options']) == 1:
    fix(data[55], ['A Bill', 'An Act', 'A Decree', 'A Regulation'],
        ['Un projet de loi', 'Une loi', 'Un décret', 'Un règlement'])
    fixed += 1; print('Fixed Q56')
# Q57 (index 56): how are MPs chosen
if 'Members of Parliament chosen' in data[56]['q'] and len(data[56]['options']) == 1:
    fix(data[56], ['Elected by Canadian citizens', 'Appointed by the Prime Minister', 'Appointed by the Queen', 'Chosen by the provinces'],
        ['Élus par les citoyens canadiens', 'Nommés par le Premier ministre', 'Nommés par la Reine', 'Choisis par les provinces'])
    fixed += 1; print('Fixed Q57')
# Q58 (index 57): who do MPs represent
if 'Members of Parliament represent' in data[57]['q'] and data[57].get('options') == ['(Multiple choice)']:
    fix(data[57], ['Everyone who lives in their electoral district', 'Only those who voted for them', 'The Prime Minister', 'The party leader'],
        ['Tous les habitants de leur circonscription électorale', 'Seulement ceux qui ont voté pour eux', 'Le Premier ministre', 'Le chef du parti'],
        q_en='Who do Members of Parliament represent?')
    fixed += 1; print('Fixed Q58')
# Q59 (index 58): how does a bill become a law
if 'bill become a law' in data[58]['q'] and len(data[58]['options']) == 1:
    fix(data[58], ['Approval by a majority in the House of Commons and Senate and finally the Governor General', 'Approval by the Prime Minister only', 'Approval by the Queen only', 'Approval by the Supreme Court'],
        ['Approbation par une majorité à la Chambre des communes et au Sénat et enfin par le gouverneur général', 'Approbation par le Premier ministre uniquement', 'Approbation par la Reine uniquement', 'Approbation par la Cour suprême'])
    fixed += 1; print('Fixed Q59')
# Q60 (index 59): three levels of government
if 'three levels of government' in data[59]['q'] and data[59].get('options') == ['(Multiple choice)']:
    fix(data[59], ['Federal, Provincial and Territorial, Municipal (local)', 'Queen, Prime Minister, Governor General', 'Legislative, Executive, Judicial', 'National, Regional, City'],
        ['Fédéral, provincial et territorial, municipal (local)', 'Reine, Premier ministre, gouverneur général', 'Législatif, exécutif, judiciaire', 'National, régional, municipal'],
        q_en='What are the three levels of government in Canada?')
    fixed += 1; print('Fixed Q60')

# Q61–Q95: batch by key phrase and len(options)==1
pairs = [
    (60, 'Name two responsibilities of the federal', ['National defence and foreign policy', 'Health and Education', 'Municipal policing', 'Driver licences'], ['Défense nationale et politique étrangère', 'Santé et éducation', 'Police municipale', 'Permis de conduire']),
    (61, 'government of all of Canada called', ['Federal', 'Provincial', 'Municipal', 'Territorial'], ['Fédéral', 'Provincial', 'Municipal', 'Territorial']),
    (62, 'right to vote in federal election', ['A Canadian citizen 18 years or older', 'Any resident', 'Only property owners', 'Only men'], ['Un citoyen canadien de 18 ans ou plus', 'Tout résident', 'Seuls les propriétaires', 'Seuls les hommes']),
    (63, 'Fathers of Confederation do', ['They worked together to establish a new country', 'They built the railway', 'They wrote the Charter', 'They elected the first PM'], ['Ils ont travaillé ensemble pour établir un nouveau pays', 'Ils ont construit le chemin de fer', 'Ils ont rédigé la Charte', 'Ils ont élu le premier PM']),
    (64, 'who must you tell how you voted', ['No one', 'Your employer', 'Elections Canada', 'The party'], ['Personne', 'Votre employeur', 'Élections Canada', 'Le parti']),
    (65, 'mark on a federal election ballot', ['An X', 'Your name', 'A check mark', 'Your signature'], ['Un X', 'Votre nom', 'Une coche', 'Votre signature']),
    (66, 'government formed after a federal election', ['The party with the most MPs forms government', 'The Queen chooses', 'The Senate decides', 'A coalition is always formed'], ['Le parti avec le plus de députés forme le gouvernement', 'La Reine choisit', 'Le Sénat décide', 'Une coalition est toujours formée']),
    (67, 'Prime Minister chosen', ['The leader of the party with the most seats', 'Elected by the people directly', 'Appointed by the Queen', 'Chosen by the Senate'], ['Le chef du parti avec le plus de sièges', 'Élu directement par le peuple', 'Nommé par la Reine', 'Choisi par le Sénat']),
    (68, 'When must federal election be held', ['At least every 4 years', 'Every 2 years', 'Every 5 years', 'When the Queen decides'], ['Au moins tous les 4 ans', 'Tous les 2 ans', 'Tous les 5 ans', 'Quand la Reine décide']),
    (69, 'Name all the federal political parties', ['Conservative, Liberal, NDP, Bloc Québécois, Green', 'Conservative and Liberal only', 'Liberal only', 'NDP and Green only'], ['Conservateur, libéral, NPD, Bloc québécois, vert', 'Conservateur et libéral seulement', 'Libéral seulement', 'NPD et vert seulement']),
    (70, 'Which party becomes the Official Opposition', ['The party with the second most MPs', 'The largest party', 'The party the Prime Minister chooses', 'The oldest party'], ['Le parti avec le deuxième plus de députés', 'Le plus grand parti', 'Le parti que le PM choisit', 'Le parti le plus ancien']),
    (71, 'role of the Opposition parties', ['To oppose or try to improve government proposals', 'To support the PM', 'To run the civil service', 'To appoint judges'], ['S\'opposer ou améliorer les propositions du gouvernement', 'Soutenir le PM', 'Diriger la fonction publique', 'Nommer les juges']),
    (72, 'Official Opposition at the federal level', ['The Conservative Party', 'The Liberal Party', 'The NDP', 'The Bloc Québécois'], ['Le Parti conservateur', 'Le Parti libéral', 'Le NPD', 'Le Bloc québécois']),
    (73, 'name of the Prime Minister of Canada', ['Justin Trudeau (Liberal Party)', 'Andrew Scheer (Conservative Party)', 'Jagmeet Singh (NDP)', 'Elizabeth May (Green Party)'], ['Justin Trudeau (Parti libéral)', 'Andrew Scheer (Parti conservateur)', 'Jagmeet Singh (NPD)', 'Elizabeth May (Parti vert)']),
    (74, 'voter information card', ['A form that tells you when and where to vote', 'A ballot', 'A citizenship card', 'A tax form'], ['Un formulaire qui indique quand et où voter', 'Un bulletin de vote', 'Une carte de citoyenneté', 'Un formulaire fiscal']),
    (75, 'right to run as a candidate in federal', ['Any Canadian citizen 18 or older', 'Only party members', 'Only property owners', 'Only those born in Canada'], ['Tout citoyen canadien de 18 ans ou plus', 'Seuls les membres du parti', 'Seuls les propriétaires', 'Seuls les nés au Canada']),
    (76, 'Canadians vote for in a federal election', ['A candidate in their riding', 'The Prime Minister directly', 'The party list', 'The Senate'], ['Un candidat dans leur circonscription', 'Le PM directement', 'La liste du parti', 'Le Sénat']),
    (77, 'federal political party is in power', ['Liberal Party', 'Conservative Party', 'NDP', 'Green Party'], ['Parti libéral', 'Parti conservateur', 'NPD', 'Parti vert']),
    (78, 'Senators chosen', ['Appointed by the Governor General', 'Elected by citizens', 'Chosen by the PM only', 'Elected by provinces'], ['Nommés par le gouverneur général', 'Élus par les citoyens', 'Choisis par le PM uniquement', 'Élus par les provinces']),
    (79, 'do not receive a voter information', ['Call Elections Canada or visit their website', 'You cannot vote', 'Go to city hall', 'Call the Prime Minister'], ['Appeler Élections Canada ou visiter leur site', 'Vous ne pouvez pas voter', 'Aller à l\'hôtel de ville', 'Appeler le PM']),
    (80, 'party forms the new government', ['The party with the most elected MPs', 'The party the Queen chooses', 'A coalition of all parties', 'The Senate decides'], ['Le parti avec le plus de députés élus', 'Le parti que la Reine choisit', 'Une coalition de tous les partis', 'Le Sénat décide']),
    (81, 'Canadians served in the First World', ['More than 600,000', 'About 100,000', 'About 50,000', 'More than 1 million'], ['Plus de 600 000', 'Environ 100 000', 'Environ 50 000', 'Plus d\'un million']),
    (82, 'Suffrage Movement', ['The effort by women to achieve the right to vote', 'The right to work', 'The right to own property', 'The right to run for office'], ['L\'effort des femmes pour obtenir le droit de vote', 'Le droit de travailler', 'Le droit de posséder', 'Le droit de se présenter']),
    (83, '1960s, Quebec experienced', ['The Quiet Revolution', 'The October Crisis', 'Confederation', 'The Great Depression'], ['La Révolution tranquille', 'La crise d\'octobre', 'La Confédération', 'La Grande Dépression']),
    (84, 'responsibilities on First Nations reserves', ['Band chiefs and councillors', 'The federal government only', 'The provincial premier', 'The RCMP only'], ['Les chefs et conseillers de bande', 'Le gouvernement fédéral uniquement', 'Le premier ministre provincial', 'La GRC uniquement']),
    (85, 'national winter sport', ['Hockey', 'Skiing', 'Curling', 'Figure skating'], ['Hockey', 'Ski', 'Curling', 'Patinage artistique']),
    (86, 'awarded the Vitoria Cross', ['99', '50', '200', '150'], ['99', '50', '200', '150']),
    (87, 'equality of women and men', ['Men and women are equal under the law', 'Women cannot vote', 'Men earn more by law', 'Only men can be PM'], ['Les hommes et les femmes sont égaux en vertu de la loi', 'Les femmes ne peuvent pas voter', 'Les hommes gagnent plus par loi', 'Seuls les hommes peuvent être PM']),
    (88, 'father of Manitoba', ['Louis Riel', 'Sir John A. Macdonald', 'Gabriel Dumont', 'Sir Wilfrid Laurier'], ['Louis Riel', 'Sir John A. Macdonald', 'Gabriel Dumont', 'Sir Wilfrid Laurier']),
    (89, 'Sir Louis-Hippolytus La Fontaine', ['A champion of democracy and responsible government', 'The first PM', 'A Father of Confederation', 'An explorer'], ['Un champion de la démocratie et du gouvernement responsable', 'Le premier PM', 'Un Père de la Confédération', 'Un explorateur']),
    (90, 'responsible government', ['The ministers must have the confidence of the elected representatives', 'The Queen rules directly', 'The PM is elected by the people', 'The Senate approves all laws'], ['Les ministres doivent avoir la confiance des élus', 'La Reine gouverne directement', 'Le PM est élu par le peuple', 'Le Sénat approuve toutes les lois']),
    (91, 'question the police', ['Yes, if you feel the need to', 'No, never', 'Only in court', 'Only with a lawyer'], ['Oui, si vous en ressentez le besoin', 'Non, jamais', 'Seulement en cour', 'Seulement avec un avocat']),
    (92, 'role of the courts in Canada', ['To settle disputes', 'To make laws', 'To run elections', 'To appoint the PM'], ['Régler les différends', 'Faire les lois', 'Organiser les élections', 'Nommer le PM']),
    (93, 'vote on election day, what do you do', ['Go to the voting station, show ID, and mark your ballot', 'Mail your ballot', 'Vote online', 'Tell the poll worker your choice'], ['Aller au bureau de vote, montrer une pièce d\'identité et marquer votre bulletin', 'Poster votre bulletin', 'Voter en ligne', 'Dire votre choix au scrutateur']),
    (94, 'two key documents that contain our rights', ['The Canadian Charter of Rights and Freedoms and Magna Carta', 'The Constitution Act 1867 only', 'The Bill of Rights (US)', 'The Criminal Code only'], ['La Charte canadienne des droits et libertés et la Magna Carta', 'La Loi constitutionnelle de 1867 uniquement', 'La Déclaration des droits (É.-U.)', 'Le Code criminel uniquement']),
    (95, 'significance of the discovery of insulin', ['Insulin has saved 16 million lives worldwide', 'It was discovered in the US', 'It cured tuberculosis', 'It was a Canadian military secret'], ['L\'insuline a sauvé 16 millions de vies dans le monde', 'Découverte aux É.-U.', 'Elle a guéri la tuberculose', 'Secret militaire canadien']),
    (96, 'three countries are signatories to NAFTA', ['Canada, Mexico and the United States', 'Canada, UK and France', 'Canada, USA and China', 'Canada, Japan and Germany'], ['Canada, Mexique et États-Unis', 'Canada, Royaume-Uni et France', 'Canada, États-Unis et Chine', 'Canada, Japon et Allemagne']),
    (97, 'June 6, 1944 invasion', ['D-Day: Allied forces invaded Normandy', 'Canada declared war', 'Vimy Ridge', 'Confederation'], ['Jour J : les Alliés ont envahi la Normandie', 'Le Canada a déclaré la guerre', 'Vimy Ridge', 'Confédération']),
    (98, 'majority government', ['When the party in power has more than half the seats', 'When the PM has a majority of votes', 'When the Senate agrees', 'When the Queen approves'], ['Quand le parti au pouvoir a plus de la moitié des sièges', 'Quand le PM a la majorité des voix', 'Quand le Sénat est d\'accord', 'Quand la Reine approuve']),
]
for idx, key, opts_en, opts_fr in pairs:
    if idx < len(data) and key in data[idx]['q'] and len(data[idx].get('options', [])) < 4:
        fix(data[idx], opts_en, opts_fr)
        fixed += 1
        print('Fixed Q' + str(idx + 1))

# Content-based fixes (key substring -> options) for duplicates and any index
content_fixes = [
    ('difference between the role of the Sovereign', ['The Sovereign is head of state; the PM is head of government', 'They are the same', 'The PM appoints the Sovereign', 'The Sovereign runs elections'], ['Le Souverain est le chef d\'État; le PM est le chef du gouvernement', 'Ils sont identiques', 'Le PM nomme le Souverain', 'Le Souverain organise les élections']),
    ('examples of taking responsibility', ['Obeying the law, volunteering, helping others', 'Only paying taxes', 'Only voting', 'Nothing'], ['Obéir à la loi, faire du bénévolat, aider les autres', 'Payer des impôts seulement', 'Voter seulement', 'Rien']),
    ('Fatima is a new immigrant', ['Equality of women and men', 'Right to vote', 'Freedom of religion', 'Right to work'], ['Égalité des hommes et des femmes', 'Droit de vote', 'Liberté de religion', 'Droit au travail']),
    ('main producer of pulp and paper', ['Quebec', 'Ontario', 'British Columbia', 'Alberta'], ['Québec', 'Ontario', 'Colombie-Britannique', 'Alberta']),
    ('Who led Quebec into Confederation', ['Sir George-Étienne Cartier', 'Sir John A. Macdonald', 'Louis Riel', 'Sir Wilfrid Laurier'], ['Sir George-Étienne Cartier', 'Sir John A. Macdonald', 'Louis Riel', 'Sir Wilfrid Laurier']),
    ('Cabinet Minister chosen', ['Chosen by the Prime Minister', 'Elected by the people', 'Appointed by the Queen', 'Chosen by the Senate'], ['Choisi par le Premier ministre', 'Élu par le peuple', 'Nommé par la Reine', 'Choisi par le Sénat']),
    ('Coat of Arms and motto', ['A Mari Usque Ad Mare (From Sea to Sea)', 'In God We Trust', 'E Pluribus Unum', 'God Save the Queen'], ['A Mari Usque Ad Mare (D\'un océan à l\'autre)', 'In God We Trust', 'E Pluribus Unum', 'God Save the Queen']),
    ('trade with other countries important', ['It creates jobs and supports our standard of living', 'It is not important', 'Only for the USA', 'Only for Europe'], ['Cela crée des emplois et soutient notre niveau de vie', 'Ce n\'est pas important', 'Seulement pour les É.-U.', 'Seulement pour l\'Europe']),
    ('Canada is a constitutional monarchy', ['The Queen or King is head of state; the PM is head of government', 'The PM is head of state', 'Canada has no monarch', 'The Queen rules directly'], ['La Reine ou le Roi est le chef d\'État; le PM est le chef du gouvernement', 'Le PM est le chef d\'État', 'Le Canada n\'a pas de monarque', 'La Reine gouverne directement']),
    ('Underground Railroad', ['An anti-slavery network that helped people escape to Canada', 'A railway in Quebec', 'A subway in Toronto', 'A road in the West'], ['Un réseau anti-esclavagiste qui a aidé des gens à fuir vers le Canada', 'Un chemin de fer au Québec', 'Un métro à Toronto', 'Une route dans l\'Ouest']),
    ('right to a secret ballot', ['No one can watch your vote or see how you voted', 'You must tell your employer', 'Only the party can see', 'Your vote is public'], ['Personne ne peut surveiller votre vote ni voir comment vous avez voté', 'Vous devez dire à votre employeur', 'Seul le parti peut voir', 'Votre vote est public']),
    ('armed uprising and seized Fort Garry', ['Louis Riel', 'Sir John A. Macdonald', 'Gabriel Dumont', 'Sir Sam Steele'], ['Louis Riel', 'Sir John A. Macdonald', 'Gabriel Dumont', 'Sir Sam Steele']),
    ('capital city of Ontario', ['Toronto', 'Ottawa', 'Hamilton', 'London'], ['Toronto', 'Ottawa', 'Hamilton', 'London']),
    ('fertile agricultural land', ['The Prairie provinces', 'British Columbia', 'The Atlantic region', 'The North'], ['Les provinces des Prairies', 'La Colombie-Britannique', 'La région de l\'Atlantique', 'Le Nord']),
    ('invented the snowmobile', ['Joseph-Armand Bombardier', 'Alexander Graham Bell', 'Sir Sandford Fleming', 'Reginald Fessenden'], ['Joseph-Armand Bombardier', 'Alexander Graham Bell', 'Sir Sandford Fleming', 'Reginald Fessenden']),
    ('industrial and manufacturing', ['Ontario', 'Quebec', 'Newfoundland', 'Saskatchewan'], ['Ontario', 'Québec', 'Terre-Neuve', 'Saskatchewan']),
    ('Victoria Cross', ['99', '50', '200', '150'], ['99', '50', '200', '150']),
    ('Victoria Cross (V.C.)', ['99', '50', '200', '150'], ['99', '50', '200', '150']),
    ('Queen\'s representative in Canada', ['The Governor General', 'The Prime Minister', 'The Premier', 'The Lieutenant Governor'], ['Le gouverneur général', 'Le Premier ministre', 'Le premier ministre provincial', 'Le lieutenant-gouverneur']),
    ('most bilingual Canadians', ['Quebec', 'New Brunswick', 'Ontario', 'Manitoba'], ['Québec', 'Nouveau-Brunswick', 'Ontario', 'Manitoba']),
    ('Senators selected', ['Appointed by the Governor General', 'Elected by citizens', 'Chosen by the PM only', 'Elected by provinces'], ['Nommés par le gouverneur général', 'Élus par les citoyens', 'Choisis par le PM uniquement', 'Élus par les provinces']),
    ('Sovereign\'s representative in the provinces', ['Lieutenant-Governor', 'Governor General', 'Premier', 'Mayor'], ['Lieutenant-gouverneur', 'Gouverneur général', 'Premier ministre provincial', 'Maire']),
    ('region covers more than one-third', ['Northern Canada', 'The Prairies', 'Central Canada', 'Atlantic Canada'], ['Le Nord du Canada', 'Les Prairies', 'Le Centre du Canada', 'Le Canada atlantique']),
    ('territories of Northern Canada', ['Yukon (Whitehorse), Northwest Territories (Yellowknife), Nunavut (Iqaluit)', 'Ontario, Quebec, Manitoba', 'BC, Alberta, Saskatchewan', 'Nova Scotia, NB, PEI'], ['Yukon (Whitehorse), Territoires du Nord-Ouest (Yellowknife), Nunavut (Iqaluit)', 'Ontario, Québec, Manitoba', 'C.-B., Alberta, Saskatchewan', 'N.-É., N.-B., Î.-P.-É.']),
    ('Canadian Pacific Railway symbolize', ['Unity', 'Trade', 'Independence', 'Wealth'], ['Unité', 'Commerce', 'Indépendance', 'Richesse']),
    ('part of the Constitution legally protects', ['The Canadian Charter of Rights and Freedoms', 'The BNA Act', 'The Criminal Code', 'The Royal Proclamation'], ['La Charte canadienne des droits et libertés', 'L\'Acte de l\'ANB', 'Le Code criminel', 'La Proclamation royale']),
    ('Sir Sam Steele', ['A great frontier hero, Mounted Policeman and soldier of the Queen', 'The first PM', 'A Father of Confederation', 'An explorer'], ['Un grand héros des frontières, policier à cheval et soldat de la Reine', 'Le premier PM', 'Un Père de la Confédération', 'Un explorateur']),
    ('Head Tax', ['Race-based entry fee charged for Chinese entering Canada', 'Income tax', 'Citizenship fee', 'Sales tax'], ['Frais d\'entrée basés sur la race pour les Chinois entrant au Canada', 'Impôt sur le revenu', 'Frais de citoyenneté', 'Taxe de vente']),
    ('Prairie provinces and their capital', ['Manitoba (Winnipeg), Saskatchewan (Regina), Alberta (Edmonton)', 'Ontario (Toronto), Quebec (Quebec City)', 'BC (Victoria), Alberta (Edmonton)', 'Nova Scotia (Halifax), NB (Fredericton)'], ['Manitoba (Winnipeg), Saskatchewan (Regina), Alberta (Edmonton)', 'Ontario (Toronto), Québec (Québec)', 'C.-B. (Victoria), Alberta (Edmonton)', 'N.-É. (Halifax), N.-B. (Fredericton)']),
    ('highest military honor', ['Victoria Cross', 'Order of Canada', 'Medal of Bravery', 'Star of Courage'], ['Croix de Victoria', 'Ordre du Canada', 'Médaille de la bravoure', 'Étoile du courage']),
    ('three oceans border Canada', ['Atlantic, Arctic and Pacific', 'Atlantic, Indian and Pacific', 'Arctic, Indian and Pacific', 'Atlantic, Pacific and Southern'], ['Atlantique, Arctique et Pacifique', 'Atlantique, Indien et Pacifique', 'Arctique, Indien et Pacifique', 'Atlantique, Pacifique et Austral']),
    ('Member of Parliament from', ['Resign so a by-election can be held', 'Stay in office', 'Appoint a replacement', 'Let the Senate decide'], ['Démissionner pour qu\'une élection partielle ait lieu', 'Rester en poste', 'Nommer un remplaçant', 'Laisser le Sénat décider']),
    ('Sir Louis-Hippolyte La Fontaine', ['A champion of democracy and responsible government', 'The first PM', 'A Father of Confederation', 'An explorer'], ['Un champion de la démocratie et du gouvernement responsable', 'Le premier PM', 'Un Père de la Confédération', 'Un explorateur']),
    ('Sir Louis- Hippolyte La Fontaine', ['A champion of democracy and responsible government', 'The first PM', 'A Father of Confederation', 'An explorer'], ['Un champion de la démocratie et du gouvernement responsable', 'Le premier PM', 'Un Père de la Confédération', 'Un explorateur']),
    ('political party is in power in Ontario', ['Liberal Party', 'Conservative Party', 'NDP', 'Green Party'], ['Parti libéral', 'Parti conservateur', 'NPD', 'Parti vert']),
    ('only officially bilingual province', ['New Brunswick', 'Quebec', 'Ontario', 'Manitoba'], ['Nouveau-Brunswick', 'Québec', 'Ontario', 'Manitoba']),
    ('Constitution Act of 1982 important', ['It patriated the Constitution and added the Charter', 'It created Confederation', 'It ended the monarchy', 'It created the Senate'], ['Il a rapatrié la Constitution et ajouté la Charte', 'Il a créé la Confédération', 'Il a aboli la monarchie', 'Il a créé le Sénat']),
    ('Nunavut become a territory', ['April 1, 1999', 'July 1, 1867', 'January 1, 2000', 'April 1, 1982'], ['1er avril 1999', '1er juillet 1867', '1er janvier 2000', '1er avril 1982']),
    ('English and French have equal status', ['In the Parliament of Canada', 'Only in Quebec schools', 'Only in federal courts', 'Only in New Brunswick'], ['Au Parlement du Canada', 'Uniquement dans les écoles du Québec', 'Uniquement dans les tribunaux fédéraux', 'Uniquement au Nouveau-Brunswick']),
    ('electoral districts are there in Canada', ['338', '308', '150', '435'], ['338', '308', '150', '435']),
    ('Vimy Ridge important', ['Canadian Corps secured its reputation for valour and bravery', 'Canada became independent', 'The war ended', 'Americans joined'], ['Le Corps canadien a assuré sa réputation de vaillance et de bravoure', 'Le Canada est devenu indépendant', 'La guerre s\'est terminée', 'Les Américains sont entrés']),
    ('equality under the law', ['Being treated with equal dignity and respect', 'Only some are equal', 'Men have more rights', 'Only citizens are equal'], ['Être traité avec une dignité et un respect égaux', 'Seuls certains sont égaux', 'Les hommes ont plus de droits', 'Seuls les citoyens sont égaux']),
    ('invented the worldwide system of standard time', ['Sir Sandford Fleming', 'Alexander Graham Bell', 'Joseph-Armand Bombardier', 'Reginald Fessenden'], ['Sir Sandford Fleming', 'Alexander Graham Bell', 'Joseph-Armand Bombardier', 'Reginald Fessenden']),
    ('major river in Quebec', ['The St. Lawrence River', 'The Fraser River', 'The Mackenzie River', 'The Saskatchewan River'], ['Le fleuve Saint-Laurent', 'Le fleuve Fraser', 'Le fleuve Mackenzie', 'La rivière Saskatchewan']),
    ('Canadian flag look like', ['White with red borders and a red maple leaf in the center', 'Blue with a Union Jack', 'Red and white with a fleur-de-lys', 'Green with a maple leaf'], ['Blanc avec des bordures rouges et une feuille d\'érable rouge au centre', 'Bleu avec un Union Jack', 'Rouge et blanc avec une fleur de lys', 'Vert avec une feuille d\'érable']),
    ('List four rights Canadian citizens have', ['Right to vote, run for office, enter and leave Canada, apply for a passport', 'Only the right to vote', 'Only the right to work', 'Only the right to travel'], ['Droit de voter, de se présenter, d\'entrer et de quitter le Canada, de demander un passeport', 'Seul le droit de voter', 'Seul le droit de travailler', 'Seul le droit de voyager']),
    ('Prairie Provinces and their capital', ['Manitoba (Winnipeg), Saskatchewan (Regina), Alberta (Edmonton)', 'Ontario (Toronto), Quebec (Quebec City)', 'BC (Victoria), Alberta (Edmonton)', 'Nova Scotia (Halifax), NB (Fredericton)'], ['Manitoba (Winnipeg), Saskatchewan (Regina), Alberta (Edmonton)', 'Ontario (Toronto), Québec (Québec)', 'C.-B. (Victoria), Alberta (Edmonton)', 'N.-É. (Halifax), N.-B. (Fredericton)']),
    ('second largest country on earth', ['True', 'False', 'Third largest', 'Fourth largest'], ['Vrai', 'Faux', 'Troisième', 'Quatrième']),
    ('most populous Atlantic Province', ['Nova Scotia', 'New Brunswick', 'Newfoundland and Labrador', 'PEI'], ['Nouvelle-Écosse', 'Nouveau-Brunswick', 'Terre-Neuve-et-Labrador', 'Î.-P.-É.']),
    ('breadbasket of the world', ['Saskatchewan', 'Manitoba', 'Alberta', 'Ontario'], ['Saskatchewan', 'Manitoba', 'Alberta', 'Ontario']),
    ('Nunavut holds the record for the coldest', ['True', 'False', 'Yukon does', 'NWT does'], ['Vrai', 'Faux', 'C\'est le Yukon', 'Ce sont les T.N.-O.']),
    ('Toronto is the capital city of Canada', ['False – Ottawa is the capital', 'True', 'Montreal is', 'Quebec City is'], ['Faux – Ottawa est la capitale', 'Vrai', 'C\'est Montréal', 'C\'est Québec']),
    ('Canada is divided in 10 regions', ['False', 'True', '5 regions', '15 regions'], ['Faux', 'Vrai', '5 régions', '15 régions']),
    ('Canada\'s largest trading partner', ['The United States', 'China', 'The United Kingdom', 'Mexico'], ['Les États-Unis', 'La Chine', 'Le Royaume-Uni', 'Le Mexique']),
    ('name Canada come', ['From Kanata, the Huron-Iroquois word for village', 'From Latin', 'From a French explorer', 'From the British Crown'], ['De Kanata, mot huron-iroquois pour village', 'Du latin', 'D\'un explorateur français', 'De la Couronne britannique']),
    ('United Empire Loyalists', ['Settlers who came from the US during and after the American Revolution', 'British soldiers', 'French colonists', 'First Nations'], ['Colons venus des É.-U. pendant et après la Révolution américaine', 'Soldats britanniques', 'Colons français', 'Premières Nations']),
    ('English settlement begin in Canada', ['Early 1600s (e.g. Newfoundland, Nova Scotia)', '1700s', '1800s', '1900s'], ['Début des années 1600 (T.-N., N.-É.)', 'Années 1700', 'Années 1800', 'Années 1900']),
    ('name Canada begin appearing on maps', ['Mid-1550s', '1600s', '1700s', '1867'], ['Milieu des années 1550', 'Années 1600', 'Années 1700', '1867']),
    ('Great Britain rename the French colony', ['The Province of Quebec', 'Upper Canada', 'Lower Canada', 'Canada East'], ['La province de Québec', 'Le Haut-Canada', 'Le Bas-Canada', 'Canada-Est']),
    ('provinces came out from the Constitutional Act', ['Upper Canada (Ontario) and Lower Canada (Quebec)', 'Nova Scotia and New Brunswick', 'Manitoba and BC', 'Alberta and Saskatchewan'], ['Haut-Canada (Ontario) et Bas-Canada (Québec)', 'Nouvelle-Écosse et Nouveau-Brunswick', 'Manitoba et C.-B.', 'Alberta et Saskatchewan']),
    ('name Canada become official', ['1867', '1791', '1840', '1982'], ['1867', '1791', '1840', '1982']),
    ('fur trade in the North West', ['The Hudson\'s Bay Company', 'The North West Company only', 'The French', 'The Americans'], ['La Compagnie de la Baie d\'Hudson', 'La Compagnie du Nord-Ouest seulement', 'Les Français', 'Les Américains']),
    ('United States launch an invasion on Canada', ['1812', '1776', '1867', '1914'], ['1812', '1776', '1867', '1914']),
    ('played an important part in building the Canadian Pacific', ['Chinese railroad workers', 'British engineers only', 'American investors', 'First Nations guides only'], ['Les travailleurs chinois du chemin de fer', 'Les ingénieurs britanniques uniquement', 'Les investisseurs américains', 'Les guides des Premières Nations uniquement']),
    ('provinces first formed Confederation', ['Nova Scotia, New Brunswick, and the Province of Canada', 'All 10 provinces', 'Ontario and Quebec only', 'BC and Alberta'], ['Nouvelle-Écosse, Nouveau-Brunswick et la province du Canada', 'Les 10 provinces', 'Ontario et Québec seulement', 'C.-B. et Alberta']),
    ('representative in Canada', ['The Governor General', 'The Prime Minister', 'The Premier', 'The Lieutenant Governor'], ['Le gouverneur général', 'Le Premier ministre', 'Le premier ministre provincial', 'Le lieutenant-gouverneur']),
    ('Sovereign\'s representative in the', ['Lieutenant-Governor', 'Governor General', 'Premier', 'Mayor'], ['Lieutenant-gouverneur', 'Gouverneur général', 'Premier ministre provincial', 'Maire']),
    ('name Canada come', ['From Kanata, the Huron-Iroquois word for village', 'From Latin', 'From a French explorer', 'From the British Crown'], ['De Kanata, mot huron-iroquois pour village', 'Du latin', 'D\'un explorateur français', 'De la Couronne britannique']),
    ('name of Canada begin appearing on maps', ['Mid-1550s', '1600s', '1700s', '1867'], ['Milieu des années 1550', 'Années 1600', 'Années 1700', '1867']),
    ('name Canada become official', ['1867', '1791', '1840', '1982'], ['1867', '1791', '1840', '1982']),
    ('War of 1812', ['Britain and its colonies (including Canada) against the United States', 'France vs Britain', 'Canada vs Britain', 'USA vs France'], ['La Grande-Bretagne et ses colonies (dont le Canada) contre les É.-U.', 'La France contre la Grande-Bretagne', 'Le Canada contre la Grande-Bretagne', 'Les É.-U. contre la France']),
    ('American attempt to conquer Canada', ['1812-1814 (War of 1812)', '1776', '1867', '1914'], ['1812-1814 (Guerre de 1812)', '1776', '1867', '1914']),
    ('Confederation mean', ['Joining of provinces to form a new country', 'The US and Canada united', 'A trade agreement', 'A military alliance'], ['L\'union des provinces pour former un nouveau pays', 'Les É.-U. et le Canada unis', 'Un accord commercial', 'Une alliance militaire']),
    ('Remembrance Day poppy', ['To remember the sacrifice of Canadians who served or died in wars', 'To celebrate Canada Day', 'To honour the monarch', 'To mark summer'], ['Se souvenir du sacrifice des Canadiens qui ont servi ou sont morts dans les guerres', 'Célébrer la fête du Canada', 'Honorer le monarque', 'Marquer l\'été']),
    ('General Sir Arthur Currie', ['Canada\'s greatest soldier in the First World War', 'A Father of Confederation', 'The first Governor General', 'A Prime Minister'], ['Le plus grand soldat canadien de la Première Guerre mondiale', 'Un Père de la Confédération', 'Le premier gouverneur général', 'Un premier ministre']),
    ('first Prime Minister of Canada', ['Sir John A. Macdonald', 'Sir Wilfrid Laurier', 'Alexander Mackenzie', 'Sir Robert Borden'], ['Sir John A. Macdonald', 'Sir Wilfrid Laurier', 'Alexander Mackenzie', 'Sir Robert Borden']),
    ('largest producer of grains and oilseeds', ['Saskatchewan', 'Alberta', 'Manitoba', 'Ontario'], ['Saskatchewan', 'Alberta', 'Manitoba', 'Ontario']),
    ('region do more than half of the people', ['Central Canada (Ontario and Quebec)', 'The Prairies', 'Atlantic Canada', 'The West'], ['Le Centre du Canada (Ontario et Québec)', 'Les Prairies', 'Le Canada atlantique', 'L\'Ouest']),
    ('five regions of Canada', ['Atlantic, Central, Prairie, West Coast, North', 'East, West, North, South, Central', '10 provinces', '5 territories'], ['Atlantique, Centre, Prairies, Côte Ouest, Nord', 'Est, Ouest, Nord, Sud, Centre', '10 provinces', '5 territoires']),
    ('provinces of Central Canada and their capi', ['Ontario (Toronto) and Quebec (Quebec City)', 'Manitoba (Winnipeg) and Saskatchewan (Regina)', 'Nova Scotia (Halifax) and New Brunswick (Fredericton)', 'Alberta (Edmonton) and BC (Victoria)'], ['Ontario (Toronto) et Québec (Québec)', 'Manitoba (Winnipeg) et Saskatchewan (Regina)', 'Nouvelle-Écosse (Halifax) et Nouveau-Brunswick (Fredericton)', 'Alberta (Edmonton) et C.-B. (Victoria)']),
    ('highest honor a Canadian can receive', ['The Order of Canada', 'Victoria Cross', 'Medal of Bravery', 'Citizenship'], ['L\'Ordre du Canada', 'Croix de Victoria', 'Médaille de la bravoure', 'Citoyenneté']),
    ('Permanent Resident of Canada has the right to vote', ['False – only citizens can vote in federal elections', 'True', 'Only in provincial elections', 'Only in municipal elections'], ['Faux – seuls les citoyens peuvent voter aux élections fédérales', 'Vrai', 'Seulement aux élections provinciales', 'Seulement aux élections municipales']),
    ('21 year old and older to be eligible', ['False – 18 years old', 'True', '19 years old', '16 years old'], ['Faux – 18 ans', 'Vrai', '19 ans', '16 ans']),
    ('party in power holds at least half of the seats', ['A majority government', 'A minority government', 'A coalition', 'Opposition'], ['Un gouvernement majoritaire', 'Un gouvernement minoritaire', 'Une coalition', 'L\'opposition']),
    ('Prime Minister and the party in power run the g', ['True', 'False', 'Only the PM', 'Only the party'], ['Vrai', 'Faux', 'Seul le PM', 'Seul le parti']),
    ('Federal government is responsible for Education', ['False – provincial responsibility', 'True', 'Municipal', 'Territorial only'], ['Faux – responsabilité provinciale', 'Vrai', 'Municipal', 'Territorial seulement']),
    ('war of 1812 with USA', ['Canada remained part of the British Empire; US did not conquer Canada', 'Canada became independent', 'USA annexed Canada', 'Britain lost'], ['Le Canada est resté dans l\'Empire britannique; les É.-U. n\'ont pas conquis le Canada', 'Le Canada est devenu indépendant', 'Les É.-U. ont annexé le Canada', 'La Grande-Bretagne a perdu']),
    ('Canadian Pacific Railway built', ['To connect Canada from sea to sea; to link BC to the rest', 'For tourism only', 'By the Americans', 'Only in the East'], ['Pour relier le Canada d\'un océan à l\'autre; pour lier la C.-B. au reste', 'Pour le tourisme seulement', 'Par les Américains', 'Seulement dans l\'Est']),
    ('Canada day', ['July 1st – anniversary of Confederation', 'July 1st – Independence', 'June 24th', 'November 11th'], ['Le 1er juillet – anniversaire de la Confédération', 'Le 1er juillet – Indépendance', 'Le 24 juin', 'Le 11 novembre']),
    ('oldest colony of the Brit', ['Newfoundland and Labrador', 'Nova Scotia', 'Ontario', 'Quebec'], ['Terre-Neuve-et-Labrador', 'Nouvelle-Écosse', 'Ontario', 'Québec']),
    ('three levels of government in Canada', ['Federal, Provincial and Territorial, Municipal (local)', 'Queen, PM, Governor General', 'Legislative, Executive, Judicial', 'National, Regional, City'], ['Fédéral, provincial et territorial, municipal (local)', 'Reine, PM, gouverneur général', 'Législatif, exécutif, judiciaire', 'National, régional, municipal']),
    ('system of government called', ['Parliamentary government', 'Presidential government', 'Direct democracy', 'Constitutional monarchy only'], ['Gouvernement parlementaire', 'Gouvernement présidentiel', 'Démocratie directe', 'Monarchie constitutionnelle seulement']),
    ('French and English do not have equal status in Parliament', ['False – they have equal status', 'True', 'Only in Quebec', 'Only in Senate'], ['Faux – ils ont un statut égal', 'Vrai', 'Seulement au Québec', 'Seulement au Sénat']),
    ('Obeying the law is', ['A responsibility of citizenship', 'Optional', 'Only for immigrants', 'Only for voters'], ['Une responsabilité de la citoyenneté', 'Optionnel', 'Seulement pour les immigrants', 'Seulement pour les électeurs']),
    ('serving on a jury is', ['A responsibility of citizenship', 'Optional', 'Only for lawyers', 'Only once'], ['Une responsabilité de la citoyenneté', 'Optionnel', 'Seulement pour les avocats', 'Une seule fois']),
    ('no compulsory military service in Canada', ['True', 'False', 'Only in wartime', 'Only for men'], ['Vrai', 'Faux', 'Seulement en temps de guerre', 'Seulement pour les hommes']),
    ('constitutional monarchy in North', ['False – Canada is not the only one', 'True', 'Canada is the only one in the world', 'There are none'], ['Faux – le Canada n\'est pas le seul', 'Vrai', 'Le Canada est le seul au monde', 'Il n\'y en a pas']),
    ('Charter of Rights and Freedom begins', ['Whereas Canada is founded upon principles that recognize the supremacy of God and the rule of law', 'We the people', 'All Canadians are equal', 'Freedom of speech'], ['Attendu que le Canada est fondé sur des principes qui reconnaissent la suprématie de Dieu et la primauté du droit', 'Nous le peuple', 'Tous les Canadiens sont égaux', 'Liberté d\'expression']),
    ('protecting and enjoying', ['Taking responsibility for oneself and one\'s family', 'Only voting', 'Only paying taxes', 'Nothing'], ['Prendre la responsabilité de soi et de sa famille', 'Voter seulement', 'Payer des impôts seulement', 'Rien']),
    ('Métis', ['The distinct Aboriginal people of mixed First Nations and European ancestry', 'First Nations only', 'Inuit only', 'European settlers'], ['Le peuple autochtone distinct d\'ascendance mixte des Premières Nations et européenne', 'Premières Nations seulement', 'Inuits seulement', 'Colons européens']),
    ('six responsibilities of citizenship', ['Vote, run for office, obey laws, serve on jury, help community, protect heritage', 'Only vote', 'Only pay taxes', 'Only work'], ['Voter, se présenter, obéir aux lois, siéger au jury, aider la communauté, protéger le patrimoine', 'Voter seulement', 'Payer des impôts seulement', 'Travailler seulement']),
    ('representative in the provi', ['Lieutenant-Governor', 'Governor General', 'Premier', 'Mayor'], ['Lieutenant-gouverneur', 'Gouverneur général', 'Premier ministre provincial', 'Maire']),
    ('From where does the name', ['From Kanata, the Huron-Iroquois word for village', 'From Latin', 'From a French explorer', 'From the British Crown'], ['De Kanata, mot huron-iroquois pour village', 'Du latin', 'D\'un explorateur français', 'De la Couronne britannique']),
    ('name of Canada begin appearing', ['Mid-1550s', '1600s', '1700s', '1867'], ['Milieu des années 1550', 'Années 1600', 'Années 1700', '1867']),
    ('name become official', ['1867', '1791', '1840', '1982'], ['1867', '1791', '1840', '1982']),
    ('begin appearing on maps', ['Mid-1550s', '1600s', '1700s', '1867'], ['Milieu des années 1550', 'Années 1600', 'Années 1700', '1867']),
    ('become official', ['1867', '1791', '1840', '1982'], ['1867', '1791', '1840', '1982']),
    ('Question #275', ['See official study guide', 'Skip this question', 'Answer A', 'Answer B'], ['Voir le guide officiel', 'Passer cette question', 'Réponse A', 'Réponse B']),
]
# Second pass: fix any remaining by matching key (from pairs or content_fixes)
for i in range(2, len(data)):
    if len(data[i].get('options', [])) >= 4:
        continue
    qtext = data[i]['q']
    for idx, key, opts_en, opts_fr in pairs:
        if key in qtext:
            fix(data[i], opts_en, opts_fr)
            fixed += 1
            print('Fixed by key Q' + str(i + 1), key[:40])
            break
    else:
        for key, opts_en, opts_fr in content_fixes:
            if key in qtext:
                fix(data[i], opts_en, opts_fr)
                fixed += 1
                print('Fixed by content Q' + str(i + 1), key[:40])
                break

with open(path, 'w', encoding='utf-8') as f:
    json.dump(data, f, ensure_ascii=False, indent=2)
print('Done. Fixed', fixed, 'questions.')
