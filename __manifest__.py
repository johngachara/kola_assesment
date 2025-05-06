{
    'name': 'RFQ_enhanced',
    'version': '1.0.2',
    'description': """
        This module extends the RFQ functionality to:
        - Allow multiple vendors per RFQ
        - Manage vendor bids
        - Select winning bids
        - Handle purchase requests
    """,
    'author': 'John Mwangi',
    'depends': ['base','purchase'],
    'data': [
        'security/security.xml',
        'security/ir.model.access.csv',
        'views/purchase_order.xml',
    ],
    'installable': True,
    'application': True,
}