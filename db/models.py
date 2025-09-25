class User(Base):
    __tablename__ = "users"
    __table_args__ = {"schema": "backend"}

    id = Column(UUID(as_uuid=True), primary_key=True)
    email = Column(String(255), nullable=False, unique=True)
    name = Column(String(255))
    photo_url = Column(Text)
    provider = Column(String(50), nullable=False)
    provider_id = Column(String(255), nullable=False)
    hashed_password = Column(String(255))
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.datetime.utcnow)
