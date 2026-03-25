*** Job Notification Service***

starting service:

pip3 install -r app_v1/requirements.txt




*** DB structure is present in schema.sql***







*** Notification service structure ***
 Producer -> Event bus -> handlers -> notification_service

How to use 
setup all components
    
```python
event_bus = EventBus()

notification_service = NotificationService()

handler = JobCreatedHandler(notification_service)

event_bus.register(EventType.JOB_EVENT, handler)

publisher = InMemoryEventPublisher(event_bus)
```

How to use publisher
```python
event = JobCreatedEvent(
    event_type=EventType.JOB_CREATED,
    job_id=1,
    tags=["python", "backend"]
)

await publisher.publish(event)
```