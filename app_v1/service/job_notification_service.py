from autogen_agentchat.messages import TextMessage
from autogen_core import CancellationToken

from app_v1.agent.tag_generation_agent import TagGenerationAgent
from app_v1.commons.service_logger import setup_logger
from app_v1.database.database_client import BaseDatabaseClient
from app_v1.database.database_config import DatabaseConfigFactory
from app_v1.database.database_manager import DatabaseManager
from app_v1.llm.llm_manager import LLMManager
from app_v1.llm.llm_model.embedding_model import EmbeddingModel
from app_v1.llm.llm_model.gpt4o_mini_llm_model import GPT4OMiniLLMModel
from app_v1.models.data_models.job_tag_response import JobTagResponse
from app_v1.service.notification_service.notification_service import NotificationService
from app_v1.service.notification_service.notification_service_helpers.event_bus import EventBus
from app_v1.service.notification_service.notification_service_helpers.event_handlers import JobEventHandler
from app_v1.service.notification_service.notification_service_helpers.event_models import EventType, JobEvent
from app_v1.service.notification_service.notification_service_helpers.event_publishers import InMemoryEventPublisher
from app_v1.service.notification_service.notification_service_helpers.notification_payload import JobNotificationPayload
from app_v1.vector_data.job_company_name_namespace import JobCompanyNameNamespace
from app_v1.vector_data.job_location_namespace import JobLocationNamespace

logger = setup_logger()


class JobNotificationService:
    # This is the main service

    def __init__(self, database_client:BaseDatabaseClient):
        self._agent = TagGenerationAgent()
        self._job_company_name_namespace = JobCompanyNameNamespace(database_client)
        self._job_location_namespace = JobLocationNamespace(database_client)

        #TODO: in future all  handler, event bus setup,etc should be at a common separate place- maybe in fastapi lifespan
        #setting up handlers and event bus for job event
        handler = JobEventHandler(database_client)
        event_bus = EventBus()
        event_bus.register_handler(EventType.JOB_EVENT, handler)

        #setting up publisher
        self._event_publisher = InMemoryEventPublisher(event_bus) #TODO: for now in memory will be enough, in future, will think about using kafka or something else

    async def generate_tags(self, job_content: str) -> JobTagResponse:

        messages = [
            TextMessage(content=job_content, source="user")
        ]
        response = await self._agent.generate_tags(messages)
        response = response.model_dump()
        return JobTagResponse(**response)

    async def generate_tags_and_send_notifications(self, job_content: str):
        try:
            job_tag_response:JobTagResponse = await self.generate_tags(job_content)
            #TODO: how to generate job link -> from llm only or can get from job_content?

            job_tag_response = await self.update_by_closest_matches(job_tag_response)
            notification_payload = JobNotificationPayload(**job_tag_response.model_dump())

            job_event = JobEvent(event_type=EventType.JOB_EVENT, job_tag_response=job_tag_response, job_notification_payload= notification_payload)
            await self._event_publisher.publish(job_event)
        except Exception as exc:
            logger.error("Error in generate_tags_and_send_notifications", exc_info=True)
            raise

    async def update_by_closest_matches(self, job_tag_response:JobTagResponse) -> JobTagResponse:

        #TODO: for now just for company_name and location, need to add for others. If best match is not found , will throw error
        best_match_job_company_names = await self._job_company_name_namespace.get_closest_matches(job_tag_response.job_company_name.lower(), 1)
        if not best_match_job_company_names:
            raise ValueError(f"No best match found for company_name: {job_tag_response.job_company_name}")
        job_tag_response.job_company_name = best_match_job_company_names[0].company_name

        best_match_job_locations = await self._job_location_namespace.get_closest_matches(job_tag_response.job_location.lower(), 1)
        if not best_match_job_locations:
            raise ValueError(f"No best match found for location: {job_tag_response.job_location}")
        job_tag_response.job_location = best_match_job_locations[0].job_location.lower()

        return job_tag_response






async def main():
    llm_manager = LLMManager()
    llm_manager.set_tag_generation_model(GPT4OMiniLLMModel())
    llm_manager.set_embedding_model(EmbeddingModel())

    database_config = DatabaseConfigFactory.create_database_config()
    database_manager = DatabaseManager(database_config)
    await database_manager.init()

    job_notification_service = JobNotificationService(database_manager.database_client)

    data = """
     "componentChunkName": "component---src-templates-job-detail-js",
    "path": "/company/careers/engineering---pipeline/senior-software-engineer---observability-7619811002",
    "result": {
        "data": {
            "drupal": {
                "paragraphsLibraryItemById": {
                    "paragraphs": {
                        "entity": {
                            "__typename": "Drupal_ParagraphSecondaryMenu",
                            "uuid": "3492f225-9d8e-424d-ab6d-deed346ffbbe",
                            "fieldTitle": "Menu",
                            "fieldLinks": [
                                {
                                    "url": {
                                        "path": "/company/careers"
                                    },
                                    "title": " Overview"
                                },
                                {
                                    "url": {
                                        "path": "/company/careers/culture?itm_data=careers-hp-nav-culture"
                                    },
                                    "title": "Culture"
                                },
                                {
                                    "url": {
                                        "path": "/company/careers/benefits?itm_data=careers-hp-nav-benefits"
                                    },
                                    "title": "Benefits"
                                },
                                {
                                    "url": {
                                        "path": "/company/careers/diversity-and-inclusion?itm_data=careers-hp-nav-diversity"
                                    },
                                    "title": "Diversity"
                                },
                                {
                                    "url": {
                                        "path": "/company/careers/engineering-at-databricks?itm_data=careers-hp-nav-engineering"
                                    },
                                    "title": "Engineering"
                                },
                                {
                                    "url": {
                                        "path": "/research#careers"
                                    },
                                    "title": "Research"
                                },
                                {
                                    "url": {
                                        "path": "/company/careers/university-recruiting?itm_data=careers-hp-nav-students"
                                    },
                                    "title": "Students & new grads"
                                }
                            ],
                            "fieldLink": null
                        }
                    }
                }
            }
        },
        "pageContext": {
            "embedGreenhouseForm": true,
            "pathname": "/company/careers/engineering---pipeline/senior-software-engineer---observability-7619811002",
            "id": "Greenhouse__Job__7619811002",
            "greenhouseId": 7619811002,
            "langPrefix": "prefix",
            "language": "EN",
            "job": {
                "id": "Greenhouse__Job__7619811002",
                "title": "Senior Software Engineer - Observability",
                "absolute_url": "https://databricks.com/company/careers/open-positions/job?gh_jid=7619811002",
                "gh_Id": 7619811002,
                "internal_job_id": 5535764002,
                "updated_at": "2026-02-19T14:47:26-05:00",
                "content": "&lt;p&gt;P-926&lt;/p&gt;\n&lt;p&gt;At Databricks, we are passionate about enabling data teams to solve the world&#39;s toughest problems — from making the next mode of transportation a reality to accelerating the development of medical breakthroughs. We do this by building and running the world&#39;s best data and AI infrastructure platform so our customers can use deep data insights to improve their business. Founded by engineers — and customer-obsessed — we leap at every opportunity to solve technical challenges, from designing next-gen UI/UX for interfacing with data to scaling our services and infrastructure across millions of virtual machines. We&#39;re only getting started in &lt;strong&gt;Bengaluru, India&lt;/strong&gt;&amp;nbsp; - and are currently in the process of setting up &lt;strong&gt;10 new teams from scratch&lt;/strong&gt;!&amp;nbsp;&lt;/p&gt;\n&lt;p&gt;Our engineering teams build technical products that fulfill real, important needs in the world. We always push the boundaries of data and AI technology, while simultaneously operating with the security and scale that is important to making customers successful on our platform.&lt;/p&gt;\n&lt;p&gt;We develop and operate one of the largest-scale software platforms. The fleet consists of millions of virtual machines, generating terabytes of logs and processing exabytes of data per day. At our scale, we observe cloud hardware, network, and operating system faults, and our software must gracefully shield our customers from any of the above.&lt;/p&gt;\n&lt;p&gt;As a software engineer in the&lt;strong&gt; Observability team&lt;/strong&gt;, you will develop observability solutions that provide insights into the health and performance of our products and infrastructure.&lt;/p&gt;\n&lt;p&gt;&amp;nbsp;&lt;/p&gt;\n&lt;p&gt;&lt;strong&gt;The impact you&#39;ll have:&lt;/strong&gt;&lt;/p&gt;\n&lt;ul&gt;\n&lt;li&gt;Establish standards for logging, metrics, and tracing.&lt;/li&gt;\n&lt;li&gt;You will collaborate with different teams to identify metrics that allow engineers to observe how well the system and different subcomponents are performing.&lt;/li&gt;\n&lt;li&gt;You will build tooling and infrastructure to allow components to efficiently emit, aggregate, and store metrics that can be displayed on dashboards and used for alerting.&lt;/li&gt;\n&lt;li&gt;Ensure the scalability, performance, and reliability of systems by contributing to and executing the technical roadmap.&lt;/li&gt;\n&lt;li&gt;Participate in on-call rotations and reduce incident response times to maintain operational excellence.&lt;/li&gt;\n&lt;li&gt;Optimize platform and infrastructure by analyzing system expenses, enhancing visibility, promoting mindful usage, enforcing retention policies, streamlining queries, and right-sizing resources to reduce observability costs.&lt;/li&gt;\n&lt;/ul&gt;\n&lt;p&gt;&lt;strong&gt;What we look for:&lt;/strong&gt;&lt;/p&gt;\n&lt;ul&gt;\n&lt;li&gt;BS (or higher) in Computer Science, or a related field.&lt;/li&gt;\n&lt;li&gt;7+ years of production-level experience in one of: Python, Java, Scala, C++, or similar languages.&lt;/li&gt;\n&lt;li&gt;Experience in software development, in large-scale distributed systems&lt;/li&gt;\n&lt;li&gt;Familiarity with metrics collection, health monitoring, and observability tools&lt;/li&gt;\n&lt;/ul&gt;&lt;div class=&quot;content-conclusion&quot;&gt;&lt;p&gt;&lt;strong&gt;About Databricks&lt;/strong&gt;&lt;/p&gt;\n&lt;p&gt;&lt;span style=&quot;font-family: arial, sans-serif;&quot;&gt;Databricks is the data and AI company. More than 10,000 organizations worldwide — including Comcast, Condé Nast, Grammarly, and over 50% of the Fortune 500 — rely on the Databricks Data Intelligence Platform to unify and democratize data, analytics and AI. Databricks is headquartered in San Francisco, with offices around the globe and was founded by the original creators of Lakehouse, Apache Spark™, Delta Lake and MLflow. To learn more, follow Databricks on&amp;nbsp;&lt;span style=&quot;color: rgb(255, 54, 33);&quot;&gt;&lt;a style=&quot;color: rgb(255, 54, 33);&quot; href=&quot;https://twitter.com/databricks&quot; target=&quot;_blank&quot; data-saferedirecturl=&quot;https://www.google.com/url?q=https://twitter.com/databricks&amp;amp;source=gmail&amp;amp;ust=1700237575733000&amp;amp;usg=AOvVaw03FL8fJvOD97ytN02f5G2C&quot;&gt;Twitter&lt;/a&gt;,&amp;nbsp;&lt;a style=&quot;color: rgb(255, 54, 33);&quot; href=&quot;https://www.linkedin.com/company/databricks&quot; target=&quot;_blank&quot; data-saferedirecturl=&quot;https://www.google.com/url?q=https://www.linkedin.com/company/databricks&amp;amp;source=gmail&amp;amp;ust=1700237575733000&amp;amp;usg=AOvVaw15dLk3q8VxTfHEgCUg7NSt&quot;&gt;LinkedIn&lt;/a&gt;&amp;nbsp;&lt;span style=&quot;color: rgb(0, 0, 0);&quot;&gt;and&lt;/span&gt;&amp;nbsp;&lt;a style=&quot;color: rgb(255, 54, 33);&quot; href=&quot;https://www.facebook.com/databricksinc&quot; target=&quot;_blank&quot; data-saferedirecturl=&quot;https://www.google.com/url?q=https://www.facebook.com/databricksinc&amp;amp;source=gmail&amp;amp;ust=1700237575733000&amp;amp;usg=AOvVaw39EcncitnlqV72EG2-RqXJ&quot;&gt;Facebook&lt;/a&gt;&lt;/span&gt;.&lt;br&gt;&lt;br&gt;&lt;strong&gt;Benefits&lt;br&gt;&lt;br&gt;&lt;/strong&gt;&lt;/span&gt;At Databricks, we strive to provide comprehensive benefits and perks that meet the needs of all of our employees. For specific details on the benefits offered in your region, please visit&amp;nbsp;&lt;a href=&quot;https://www.mybenefitsnow.com/databricks&quot;&gt;https://www.mybenefitsnow.com/databricks&lt;/a&gt;.&amp;nbsp;&lt;br&gt;&lt;br&gt;&lt;/p&gt;\n&lt;p&gt;&lt;strong&gt;Our Commitment to Diversity and Inclusion&lt;/strong&gt;&lt;/p&gt;\n&lt;p&gt;At Databricks, we are committed to fostering a diverse and inclusive culture where everyone can excel. We take great care to ensure that our hiring practices are inclusive and meet equal employment opportunity standards. Individuals looking for employment at Databricks are considered without regard to age, color, disability, ethnicity, family or marital status, gender identity or expression, language, national origin, physical and mental ability, political affiliation, race, religion, sexual orientation, socio-economic status, veteran status, and other protected characteristics.&lt;/p&gt;\n&lt;p&gt;&lt;strong&gt;Compliance&lt;/strong&gt;&lt;/p&gt;\n&lt;p&gt;&lt;strong&gt;&lt;span style=&quot;font-weight: 400;&quot;&gt;If access to export-controlled technology or source code is required for performance of job duties, it is within Employer&#39;s discretion whether to apply for a U.S. government license for such positions, and Employer may decline to proceed with an applicant on this basis alone.&lt;/span&gt;&lt;/strong&gt;&lt;/p&gt;&lt;/div&gt;",
                "offices": [
                    {
                        "name": "Bengaluru, India"
                    }
                ],
                "location": {
                    "name": "Bengaluru, India"
                },
                "departments": [
                    {
                        "name": "Engineering - Pipeline"
                    }
                ],
                "metadata": [
                    {
                        "value": "Databricks India Private Limited",
                        "filterDept": "D"
                    },
                    {
                        "value": [
                            "Engineering"
                        ],
                        "filterDept": "Engineering"
                    }
                ]
            }
        }
    },
    "staticQueryHashes": [
        "2197321345",
        "3834171261",
        "527633433",
        "69577834"
    ],
    "slicesMap": {}
}
     """
    await job_notification_service.generate_tags_and_send_notifications(data)
    print("done")

if __name__ == "__main__":
    import asyncio
    asyncio.run(main())



