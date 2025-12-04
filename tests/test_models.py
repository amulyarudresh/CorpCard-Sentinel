from corpcard_sentinel.models import User, Policy, Transaction, CardStatus

def test_create_user(db_session):
    user = User(name="Alice", email="alice@example.com", card_status=CardStatus.ACTIVE)
    db_session.add(user)
    db_session.commit()
    
    assert user.id is not None
    assert user.name == "Alice"
    assert user.card_status == CardStatus.ACTIVE

def test_create_policy(db_session):
    policy = Policy(rule_name="Test Rule", description="Test Description", is_active=True)
    db_session.add(policy)
    db_session.commit()
    
    assert policy.id is not None
    assert policy.rule_name == "Test Rule"
    assert policy.is_active is True

def test_create_transaction(db_session, sample_user):
    tx = Transaction(
        user_id=sample_user.id,
        merchant="Test Merchant",
        amount=50.0,
        category="Food",
        is_violation=False
    )
    db_session.add(tx)
    db_session.commit()
    
    assert tx.id is not None
    assert tx.user_id == sample_user.id
    assert tx.amount == 50.0
