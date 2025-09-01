import logging
from dynaconf import Dynaconf
from pathlib import Path
from tag_extractor import Gen_AI_Tagextractor_LLMOnly

def main():
 
    config = Dynaconf(
    envvar_prefix=False,  # do not require export prefix
    settings_files=[str(Path(".env").resolve())],  # explicitly load your .env file
    load_dotenv=True,
    )

    print(config.get("SNOWFLAKE__ACCOUNT"))

    extractor = Gen_AI_Tagextractor_LLMOnly(config)

    sample_text = """<h3>Introduction</h3>\n<p>Many leadership styles exist,
    but those with elements that centralize around relationships remain the preferred style by many nurses and healthcare teams. 
    More specifically, evidence suggests that nurses prefer relationship-oriented leaders who practice consistently from the positive leadership perspective (Alilyyani et al., 2018). 
    Nurses also want to have relationships with their leaders and feel valued (Armstrong et al., 2021). 
    Evidence from multiple international studies suggests that leaders who practice from a positive leadership style favorably influence the patient’s experience, 
    patient outcomes, and workforce indicators, including RN retention, reduced turnover,
    and nurse satisfaction (Alilyyani et al., 2018; Northouse, 2019; Oberleitner, 2019; Porter-O’Grady &amp; Malloch, 2018; Saleh et al., 2018; Wong &amp; Cummings, 2009).
    </p>\n<p>The American Organization for Nursing Leadership (2015) established core competencies for nurse executives and leaders, including relational proficiency, creating a trusting environment, and mentorship. 
    These three competencies serve as some of the essential elements for relational leadership practice. 
    Relational leadership implies that a leader’s effectiveness is based on the leader’s ability to create and maintain productive working relationships with others within an organization. 
    In relational leadership, the context of leadership is wholly encompassed by these relationships developed and maintained between the leader and the leader’s followers (Wheatley, 2006). 
    Although relationships between the leader and followers are highly valued (Clarke, 2018), little attention is given to the role of effective mentoring as an essential component of relational leadership. 
    Because the leader–follower relationship is based on the need for the leader to formally or informally mentor followers at some point in the professional relationship, 
    it is essential for leaders who practice relational leadership to understand and appreciate the need for effective mentorship (Goodyear &amp; Goodyear, 2018). 
    Therefore, the purpose of this section of the case study is to describe how effective mentoring in nursing is congruent with relational leadership.</p>'"""
    tags = extractor.extract_tags(sample_text, "reading")

    print(tags)


if __name__ == "__main__":
    main()
