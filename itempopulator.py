# itempopulator.py
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from database_setup import Base, Category, Item, User
import datetime


engine = create_engine('sqlite:///categoryitemswithuser.db')
Base.metadata.create_all(engine)
DBSession = sessionmaker(bind=engine)
session = DBSession()

user1 = User(name="Robo Barista", email="tinnyTim@example.com",
  picture="http://s3.amazonaws.com/37assets/svn/765-default-avatar.png")
session.add(user1)
session.commit()

user2 = User(name="Frank Miller", email="frankmiller@example.com",
  picture="http://s3.amazonaws.com/37assets/svn/765-default-avatar.png")
session.add(user2)
session.commit()

user3 = User(name="Robert De Naro", email="roberdenaro@example.com",
  picture="http://s3.amazonaws.com/37assets/svn/765-default-avatar.png")
session.add(user3)
session.commit()

user4 = User(name="Sarah Burton", email="sarahburton@example.com",
  picture="http://s3.amazonaws.com/37assets/svn/765-default-avatar.png")
session.add(user4)
session.commit()

cat1 = Category(name="Philosophy", user=user1)
session.add(cat1)
session.commit()

item1 = Item(name="Theory of philosophy", 
             description="Philosophical method is the study of how to do philosophy. A common view among philosophers is that philosophy is distinguished by the ways that philosophers follow in addressing philosophical questions. There is not just one method that philosophers use to answer philosophical questions.",
             category=cat1,
             user=user1)
session.add(item1)
session.commit()

item2 = Item(name="Organizations of philosophy",
             description="List of philosophical organizations and societies",
             category=cat1,
             user=user2)
session.add(item2)
session.commit()

cat2 = Category(name="Metaphysics", user=user2)
session.add(cat2)
session.commit()

item3 = Item(name="Ontology",
             description="Ontology is the philosophical study of the nature of being, becoming, existence, or reality, as well as the basic categories of being and their relations.",
             category=cat2,
             user=user3)
session.add(item3)
session.commit()

item4 = Item(name="Cosmology",
             description="Cosmology is the study of the origin, evolution, and eventual fate of the universe. Physical cosmology is the scholarly and scientific study of the origin, evolution, large-scale structures and dynamics, and ultimate fate of the universe, as well as the scientific laws that govern these realities.",
             category=cat2,
             user=user4)
session.add(item4)
session.commit()

item5 = Item(name="Space and time",
             description="Philosophy of space and time is the branch of philosophy concerned with the issues surrounding the ontology, epistemology, and character of space and time. While such ideas have been central to philosophy from its inception, the philosophy of space and time was both an inspiration for and a central aspect of early analytic philosophy.",
             category=cat2,
             user=user1)
session.add(item5)
session.commit()

cat3 = Category(name="Episotemology", user=user3)
session.add(cat3)
session.commit()

item6 = Item(name="Determinism and indeterminism",
             description="Determinism is the philosophical position that for every event, including human action, there exist conditions that could cause no other event.",
             category=cat3,
             user=user2)
session.add(item6)
session.commit()

item7 = Item(name="The self",
             description="The philosophy of self defines the essential qualities that make one person distinct from all others. There have been numerous approaches to defining these qualities. The self is the idea of a unified being which is the source of consciousness.",
             category=cat3,
             user=user3)
session.add(item7)
session.commit()

cat4 = Category(name="Parapsychology", user=user4)
session.add(cat4)
session.commit()

item8 = Item(name="Physiognomy",
             description="Physiognomy is the assessment of a person's character or personality from his or her outer appearance, especially the face. The term can also refer to the general appearance of a person, object, or terrain, without reference to its implied characteristics, as in the physiognomy of a plant community.",
             category=cat4,
             user=user4)
session.add(item8)
session.commit()

item9 = Item(name="Phrenology",
             description= "Phrenology is a pseudoscience primarily focused on measurements \
                   of the human skull, based on the concept that the brain is the organ of the mind, and that certain brain areas have localized, specific functions or modules.",
             category=cat4,
             user=user1)
session.add(item9)
session.commit()

cat5 = Category(name="Psychology", user=user1)
session.add(cat5)
session.commit()

item10 = Item(name="Subconscious",
              description="In psychology, the subconscious is the part of consciousness that is not currently in focal awareness. The word 'subconscious' represents an anglicized version of the French subconscient as coined by the psychologist Pierre Janet (1859-1947), who argued that underneath the layers of critical-thought functions of the conscious mind lay a powerful awareness that he called the subconscious mind. Carl Jung said that there is a limit to what can be held in conscious focal awareness, an alternative storehouse of one's knowledge and prior experience is needed.[",
              category=cat5,
             user=user2)
session.add(item10)
session.commit()

item11 = Item(name="Comparative psychology",
              description="Comparative psychology refers to the scientific study of the behavior, and mental processes of non-human animals, especially as these relate to the phylogenetic history, adaptive significance, and development of behavior. Research in this area addresses many different issues, uses many different methods, and explores the behavior of many different species, from insects to primates.",
              category=cat5,
             user=user3)
session.add(item11)
session.commit()

cat6 = Category(name="Philosophical Logic", user=user2)
session.add(cat6)
session.commit()

item12 = Item(name="Induction",
              description="Inductive reasoning (as opposed to deductive reasoning or abductive reasoning) is reasoning in which the premises seek to supply strong evidence for (not absolute proof of) the truth of the conclusion. While the conclusion of a deductive argument is certain, the truth of the conclusion of an inductive argument is probable, based upon the evidence given.",
              category=cat6,
             user=user4)
session.add(item12)
session.commit()

item13 = Item(name="Deduction",
              description="Deductive reasoning, also deductive logic or logical deduction or, informally, 'top-down' logic, is the process of reasoning from one or more statements (premises) to reach a logically certain conclusion.",
              category=cat6,
             user=user1)
session.add(item13)
session.commit()

cat7 = Category(name="Ethics", user=user3)
session.add(cat7)
session.commit()

item14 = Item(name="Family relationships",
              description="In the context of human society, a family (from Latin: familia) is a group of people affiliated by consanguinity (by recognized birth), affinity (by marriage), or co-residence and/or shared consumption (see Nurture kinship). Members of the immediate family includes spouses, parents, brothers, sisters, sons and/or daughters. Members of the extended family may include grandparents, aunts, uncles, cousins, nephews nieces and/or siblings-in-law.",
              category=cat7,
             user=user2)
session.add(item14)
session.commit()

cat8 = Category(name="Ancient, medieval & Eastern philosophy", user=user4)
session.add(cat8)
session.commit()

item15 = Item(name="Pre-Socratic Greek philosophies",
              description="Pre-Socratic philosophy is Greek philosophy before Socrates (and includes schools contemporary with Socrates that were not influenced by him).",
              category=cat8,
             user=user3)
session.add(item15)
session.commit()

cat0 = Category(name="Unclassified", user=user1)
session.add(cat0)
session.commit()