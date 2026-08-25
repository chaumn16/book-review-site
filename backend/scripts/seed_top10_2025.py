"""Seed the database with the New York Times' "10 Best Books of 2025".

Content (summary + section highlights) was written directly rather than via
the Anthropic API (no key needed to run this) — same spirit as the app's own
generation prompt: honest, general-knowledge overviews rather than invented
specifics for books/chapters we're not certain about.

Run from the backend/ directory with the venv active:
    python scripts/seed_top10_2025.py
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.database import Base, SessionLocal, engine  # noqa: E402
from app.models import Book, ChapterHighlight  # noqa: E402

SEED_BOOKS = [
    {
        "title": "Angel Down",
        "author": "Daniel Kraus",
        "summary": (
            "A horror novel set in the trenches of World War I: a company of soldiers finds a "
            "wounded, otherworldly figure amid the wreckage of a crash in No Man's Land, and drags "
            "it back to their lines uncertain whether they've captured a weapon, a prisoner, or a "
            "miracle. As command takes interest and pressure mounts to use the captive against the "
            "German trenches, the unit fractures over what the being really is — angelic, demonic, "
            "or something with no name at all. Kraus juxtaposes the visceral brutality of trench "
            "warfare with an ambiguous, monstrous-yet-divine presence, asking what ordinary men do "
            "when they capture something they can neither understand nor control. It's as much a war "
            "novel as a horror one, using the fantastical premise to sharpen its portrait of faith, "
            "fear, and atrocity under unbearable pressure."
        ),
        "chapters": [
            (1, "The Crash", "A star falls into No Man's Land, and a scouting party finds a wounded, otherworldly figure amid the wreckage."),
            (2, "Capture", "The soldiers drag the being back to their trench, uncertain whether they've found a weapon, a prisoner, or a miracle."),
            (3, "Interrogation", "Command takes interest, and the company is ordered to keep the creature alive and extract whatever it knows."),
            (4, "Faith and Fear", "Religious soldiers wrestle with whether the being is angelic or demonic, splitting loyalties within the unit."),
            (5, "Escalation", "As the front worsens, pressure mounts to use the captive as a weapon against the German lines."),
            (6, "The Reveal", "The being's true nature and motives come into sharper, more disturbing focus."),
            (7, "Breaking Point", "Violence within the trench mirrors the violence outside it as the soldiers' plan spirals."),
            (8, "Aftermath", "The novel closes on the human cost of trying to control something beyond comprehension."),
        ],
        "verdict": {
            "label": "depends",
            "reason": (
                "A gripping, inventive premise for horror and war-fiction fans, but the graphic violence and unrelenting bleakness make it a hard sell if that's not already your genre."
            ),
        },
    },
    {
        "title": "The Director",
        "author": "Daniel Kehlmann",
        "summary": (
            "A historical novel centered on G.W. Pabst, the celebrated Austrian film director who "
            "returned to Nazi Germany in 1939 after a trip abroad, and the moral compromises he made "
            "to keep working under the Third Reich. Kehlmann traces Pabst's descent from an "
            "internationally admired auteur into a filmmaker complicit with a monstrous regime, "
            "exploring the seduction of art, status, and self-justification. The novel moves between "
            "Pabst's household, his film sets, and the machinery of Nazi propaganda, showing how small, "
            "individually defensible decisions compound into full complicity. Rather than a simple "
            "villain's tale, it's a study of how a talented, not-unsympathetic man rationalizes his way "
            "into service of a regime he privately despises — and what that costs the people around him."
        ),
        "chapters": [
            (1, "The Return", "Pabst travels back to Austria for a family matter as war looms, then finds himself trapped when the borders close."),
            (2, "Old Glory", "Flashbacks establish Pabst's prewar career and the prestige he's used to commanding."),
            (3, "The New Regime", "Pabst is pulled into the Nazi film industry, first reluctantly, then more willingly."),
            (4, "Compromises", "Small accommodations to the regime pile up, each easier to justify than the last."),
            (5, "The Family", "Pabst's wife and son bear the emotional weight of his choices at home."),
            (6, "On Set", "Kehlmann depicts the surreal experience of making films under state control and surveillance."),
            (7, "Reckoning", "As the war turns and the regime's crimes become undeniable, Pabst confronts what he's become."),
            (8, "Legacy", "The novel closes on the ambiguous historical judgment of a talented man who chose survival and status over resistance."),
        ],
        "verdict": {
            "label": "worth_it",
            "reason": (
                "A sharp, unsettling character study of moral compromise that rewards readers interested in WWII history and literary fiction, even without prior knowledge of Pabst's films."
            ),
        },
    },
    {
        "title": "The Loneliness of Sonia and Sunny",
        "author": "Kiran Desai",
        "summary": (
            "A sprawling love story following two young Indians — Sonia, an aspiring writer, and "
            "Sunny, adrift and searching for purpose — whose paths intersect and diverge across India, "
            "the US, and beyond over many years. Desai, author of the Booker Prize-winning The "
            "Inheritance of Loss, returns to her signature themes of migration, class, and the gap "
            "between ambition and belonging, tracing how family expectation, distance, and timing keep "
            "pulling the two apart even as they're drawn together. It's as much a portrait of "
            "contemporary global Indian identity, and the particular loneliness of living between "
            "countries, as it is a will-they-won't-they romance."
        ),
        "chapters": [
            (1, "Beginnings", "Sonia and Sunny's childhoods and families are introduced, setting up very different worlds."),
            (2, "First Crossing", "The two meet, and an immediate, complicated connection forms."),
            (3, "Separate Paths", "Ambition and family obligation send them to different countries and different lives."),
            (4, "Sonia Abroad", "Sonia navigates writing, identity, and loneliness far from home."),
            (5, "Sunny's Drift", "Sunny struggles to find footing and purpose, chasing reinvention."),
            (6, "Near Misses", "The two circle each other across years, timing never quite aligning."),
            (7, "Reckoning with Family", "Both confront what their parents and homelands expect of them."),
            (8, "Return", "The novel moves toward a reunion shaped by everything that's happened in between."),
        ],
        "verdict": {
            "label": "worth_it",
            "reason": (
                "Desai's long-awaited follow-up delivers the same emotional precision and social insight as The Inheritance of Loss; especially worth it if you enjoy slow-building, character-driven literary fiction."
            ),
        },
    },
    {
        "title": "The Sisters",
        "author": "Jonas Hassen Khemiri",
        "summary": (
            "A multigenerational family saga from Swedish author Jonas Hassen Khemiri, following a "
            "family of sisters whose lives, secrets, and inherited histories are examined through "
            "shifting perspectives and time periods. Khemiri, known for playful, structurally inventive "
            "prose, uses the sisters' divergent lives to interrogate identity, immigration, and the "
            "stories families tell — and hide — about themselves. As one sister's crisis pulls the "
            "others back together, buried history resurfaces and forces a reckoning with how each of "
            "them became who they are. General overview based on available information; exact chapter "
            "structure may differ from the summary below."
        ),
        "chapters": [
            (1, "The Gathering", "An event or crisis draws the sisters back into each other's orbit."),
            (2, "Sister One's Story", "The eldest's version of the family history is laid out."),
            (3, "Sister Two's Story", "A second sister's account complicates or contradicts the first."),
            (4, "Sister Three's Story", "A third perspective reveals what's been left unsaid."),
            (5, "The Parents", "The family's older generation and their choices come into focus."),
            (6, "Buried History", "Secrets that shaped the sisters' upbringing surface."),
            (7, "Confrontation", "The sisters address what's been avoided for years."),
            (8, "Aftermath", "The novel closes on a reconfigured, if not fully resolved, family bond."),
        ],
        "verdict": {
            "label": "depends",
            "reason": (
                "Khemiri's structural playfulness and multigenerational family drama will appeal to readers who enjoy literary puzzle-box narratives, but the fragmented, multi-perspective structure asks for patience."
            ),
        },
    },
    {
        "title": "Stone Yard Devotional",
        "author": "Charlotte Wood",
        "summary": (
            "An unnamed woman leaves her life and job behind to retreat to a remote monastery in rural "
            "New South Wales, seeking quiet and distance from a world she can no longer bear — "
            "including looming ecological collapse. Her stay is interrupted by a mouse plague "
            "overrunning the region and the return of a figure from the community's past, whose "
            "presence forces the narrator to confront grief, guilt, and unresolved questions of faith "
            "she thought she'd left behind. Wood's novel, shortlisted for the Booker Prize, is a spare, "
            "interior meditation on mortality, environmental anxiety, and what it means to seek meaning "
            "without belief."
        ),
        "chapters": [
            (1, "Arrival", "The narrator settles into the monastery, drawn by a need for stillness."),
            (2, "Daily Rhythms", "Life among the nuns establishes a contemplative, ascetic rhythm."),
            (3, "The Plague", "A biblical-scale mouse infestation disrupts the community's peace."),
            (4, "Ghosts of the Past", "Memories of the narrator's mother and a lost friend surface."),
            (5, "The Visitor", "A figure tied to a past controversy arrives, unsettling the community."),
            (6, "Faith Examined", "The narrator wrestles with belief, doubt, and why she's really there."),
            (7, "Reckoning", "Old guilt and grief come to a head against the backdrop of the plague."),
            (8, "Stillness", "The novel ends in quiet, unresolved reflection rather than easy answers."),
        ],
        "verdict": {
            "label": "depends",
            "reason": (
                "A beautifully spare, meditative novel that Booker judges loved, but its slow pace and lack of plot momentum mean it's best suited to readers who want interiority over incident."
            ),
        },
    },
    {
        "title": "A Marriage at Sea: A True Story of Love, Obsession, and Shipwreck",
        "author": "Sophie Elmhirst",
        "summary": (
            "The true story of Maurice and Maralyn Bailey, a British couple who sold their possessions "
            "in the 1970s to sail around the world, only to have their boat sunk by a whale in the "
            "Pacific. Elmhirst reconstructs their months adrift in a small life raft and dinghy — "
            "battling starvation, despair, and each other — and the stranger, more complicated story of "
            "what happened to their marriage after they were finally rescued. It's a survival story and, "
            "just as much, an unflinching portrait of a long marriage under the most extreme possible "
            "pressure."
        ),
        "chapters": [
            (1, "Setting Sail", "Maurice and Maralyn give up ordinary life for a dream of the open sea."),
            (2, "The Wreck", "Their boat is struck and sunk, forcing them into a tiny life raft."),
            (3, "Adrift", "Days turn to weeks as they ration food, catch rainwater, and fight to survive."),
            (4, "The Marriage Under Pressure", "Isolation and desperation strain their relationship in new ways."),
            (5, "Rescue", "After months at sea, they are finally spotted and saved."),
            (6, "Return to Land", "Readjusting to ordinary life proves its own kind of difficult."),
            (7, "Aftermath", "Elmhirst traces what survival cost them, and what it meant for their marriage afterward."),
            (8, "Legacy", "The book closes on how the Baileys' ordeal came to be remembered."),
        ],
        "verdict": {
            "label": "worth_it",
            "reason": (
                "A tightly told, genuinely gripping survival story that doubles as an unusually honest portrait of a marriage -- accessible even if you don't normally read nonfiction."
            ),
        },
    },
    {
        "title": "Mother Emanuel",
        "author": "Kevin Sack",
        "summary": (
            "A sweeping history of Charleston's Mother Emanuel AME Church — one of the oldest Black "
            "churches in the American South — tracing its origins in slavery and its role in the fight "
            "for civil rights, up through the 2015 massacre in which a white supremacist murdered nine "
            "congregants during Bible study. Sack, a Pulitzer Prize-winning journalist, weaves together "
            "centuries of history with the personal stories of victims, survivors, and the broader "
            "Charleston community, situating the shooting within the church's long, embattled history "
            "rather than treating it as an isolated tragedy."
        ),
        "chapters": [
            (1, "Origins", "The church's founding amid slavery and its early, dangerous existence."),
            (2, "Suppression and Survival", "Efforts by white authorities to shut the church down across generations."),
            (3, "Civil Rights Era", "Mother Emanuel's role as a hub of Black organizing and resistance."),
            (4, "Modern Congregation", "The community and leadership in the years leading up to 2015."),
            (5, "The Shooting", "A detailed account of the June 2015 massacre."),
            (6, "The Victims", "Portraits of the nine people killed."),
            (7, "Forgiveness and Fury", "The community's public response, including the widely covered forgiveness of the shooter."),
            (8, "Aftermath", "The church and Charleston's reckoning with race and history in the years since."),
        ],
        "verdict": {
            "label": "worth_it",
            "reason": (
                "A meticulously reported, important history that goes well beyond the 2015 shooting most readers already know about -- essential if you want to understand the church and community, not just the tragedy."
            ),
        },
    },
    {
        "title": "Mother Mary Comes to Me",
        "author": "Arundhati Roy",
        "summary": (
            "Arundhati Roy's memoir of her fraught, formative relationship with her mother, Mary Roy — "
            "a fierce, unconventional educator and activist in Kerala who fought a landmark legal battle "
            "for women's inheritance rights, and who was, by Roy's account, as difficult to love as she "
            "was impossible to ignore. The book moves between Roy's childhood in a small Kerala town, "
            "her mother's own rebellion against convention, and Roy's path to becoming a writer and "
            "activist in her own right — tracing how a complicated, sometimes painful maternal bond "
            "shaped the woman who would write The God of Small Things and become one of India's most "
            "prominent public intellectuals."
        ),
        "chapters": [
            (1, "A Difficult Inheritance", "Roy introduces her mother's outsized, contradictory presence in her life."),
            (2, "Kerala Childhood", "Growing up in Mary Roy's unconventional household and school."),
            (3, "Mary's Rebellion", "Mary Roy's own fight against social convention and the law."),
            (4, "Leaving Home", "Roy's departure and early independence from her mother's orbit."),
            (5, "Becoming a Writer", "Roy's path toward The God of Small Things and public life."),
            (6, "Public Battles", "Mother and daughter as two formidable, often colliding, public figures."),
            (7, "Reconciliation", "Moments of tenderness and understanding amid the conflict."),
            (8, "Legacy", "Roy reflects on what she inherited from a mother she both resisted and became."),
        ],
        "verdict": {
            "label": "worth_it",
            "reason": (
                "Roy brings the same precise, emotionally exacting prose from The God of Small Things to her own life; worth it for her fans and for anyone interested in a complicated mother-daughter story."
            ),
        },
    },
    {
        "title": "There Is No Place for Us: Working and Homeless in America",
        "author": "Brian Goldstone",
        "summary": (
            "An investigative account following several families in Atlanta who work full-time jobs yet "
            "remain homeless — sleeping in extended-stay motels, cars, or shelters — exposing what "
            "Goldstone calls America's hidden homelessness crisis. Through years of embedded reporting, "
            "he shows how stagnant wages, predatory housing costs, and a fraying safety net have pushed "
            "the working poor into precarity even as they clock in every day, challenging the assumption "
            "that homelessness is primarily about unemployment or addiction. The book combines intimate "
            "family portraits with policy analysis of how American housing markets got this way."
        ),
        "chapters": [
            (1, "Working and Homeless", "Goldstone introduces the families and the paradox at the book's center."),
            (2, "Britt's Story", "One family's cycle through motels, shelters, and precarious jobs."),
            (3, "Maurice's Story", "A second family confronts the gap between full-time work and stable housing."),
            (4, "The Motel Economy", "How extended-stay motels became a shadow housing system for the poor."),
            (5, "Policy Failures", "Goldstone traces the housing and welfare policy decisions that created this crisis."),
            (6, "Children in the System", "The particular toll of housing instability on kids."),
            (7, "Attempts at Escape", "Families' efforts to break the cycle, and what gets in the way."),
            (8, "A Broader Reckoning", "The book closes by connecting individual stories to national housing policy."),
        ],
        "verdict": {
            "label": "worth_it",
            "reason": (
                "Rigorously reported and humanizing without being sentimental -- one of the more important works of journalism on this list if you care about housing and labor policy in America."
            ),
        },
    },
    {
        "title": "Wild Thing: A Life of Paul Gauguin",
        "author": "Sue Prideaux",
        "summary": (
            "A biography of the French Post-Impressionist painter Paul Gauguin, tracing his path from a "
            "failed stockbroker to one of the most influential — and most controversial — artists of the "
            "19th century. Prideaux follows Gauguin from Paris and his fraught friendship with Van Gogh, "
            "through his self-exile to Tahiti and the Marquesas Islands in search of an 'unspoiled' life "
            "and art, examining both his radical artistic achievements and the exploitative, colonial "
            "realities of his life abroad that have made him an increasingly contested figure. The book "
            "aims for a clear-eyed portrait that neither lionizes nor simply cancels a complicated, "
            "era-defining artist."
        ),
        "chapters": [
            (1, "The Stockbroker", "Gauguin's unlikely early life before he turned to painting."),
            (2, "Into the Avant-Garde", "His entry into the Impressionist and Post-Impressionist circles in Paris."),
            (3, "Van Gogh", "The intense, combustible friendship and collaboration between the two painters."),
            (4, "Leaving Europe", "Gauguin's decision to abandon his family and career for the South Pacific."),
            (5, "Tahiti", "His years painting in Tahiti and the complicated reality behind his idyllic canvases."),
            (6, "The Marquesas", "A further retreat, deteriorating health, and conflict with colonial authorities."),
            (7, "Legacy and Controversy", "Prideaux weighs Gauguin's artistic influence against the ethical questions raised by his life."),
            (8, "Final Years", "Gauguin's death in the Marquesas and the myth that grew up around him."),
        ],
        "verdict": {
            "label": "depends",
            "reason": (
                "A clear-eyed, well-researched biography that doesn't shy from Gauguin's troubling colonial conduct, but general readers not already interested in art history or Gauguin specifically may find its detail more than they need."
            ),
        },
    },
]


def main():
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    added, updated, skipped = 0, 0, 0
    try:
        for entry in SEED_BOOKS:
            existing = (
                db.query(Book)
                .filter(Book.title == entry["title"], Book.author == entry["author"])
                .first()
            )
            if existing:
                # Idempotent backfill: fills in a verdict for books seeded
                # before this field existed, without touching anything else
                # (in case the summary/chapters were hand-edited since).
                if not existing.verdict_label:
                    existing.verdict_label = entry["verdict"]["label"]
                    existing.verdict_reason = entry["verdict"]["reason"]
                    db.commit()
                    print(f"updated verdict for existing book: {entry['title']!r}")
                    updated += 1
                else:
                    print(f"skip (already present): {entry['title']!r} by {entry['author']}")
                    skipped += 1
                continue

            book = Book(
                title=entry["title"],
                author=entry["author"],
                summary=entry["summary"],
                status="ready",
                verdict_label=entry["verdict"]["label"],
                verdict_reason=entry["verdict"]["reason"],
            )
            db.add(book)
            db.flush()  # assigns book.id

            for chapter_number, chapter_title, highlight in entry["chapters"]:
                db.add(
                    ChapterHighlight(
                        book_id=book.id,
                        chapter_number=chapter_number,
                        chapter_title=chapter_title,
                        highlight=highlight,
                    )
                )
            db.commit()
            print(f"added: {entry['title']!r} by {entry['author']} ({len(entry['chapters'])} sections)")
            added += 1
    finally:
        db.close()

    print(f"\nDone. {added} added, {updated} updated with a backfilled verdict, {skipped} already up to date.")


if __name__ == "__main__":
    main()
