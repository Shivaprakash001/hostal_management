# Hostel Management System - Payments Module

## Overview

The Payments Module is a comprehensive solution for managing hostel payments, including student payment portals, admin dashboards, PDF receipt generation, and CSV export functionality. Built using FastAPI, SQLAlchemy, and ReportLab for PDF generation.

## Features

### 🎓 Student Side
- **Payment Portal**: View monthly rent dues and payment history
- **Mark as Paid**: Simulate payment completion with payment method selection
- **Download Receipt**: Generate and download PDF receipts for completed payments
- **Payment History**: View all past payments with status and details

### 👨‍💼 Admin Side
- **Payment Dashboard**: Comprehensive view of all payments with statistics
- **Advanced Filtering**: Filter by month, year, payment status, and student
- **Payment Management**: Add, edit, and delete payment records
- **CSV Export**: Export payment data for external analysis
- **Payment Statistics**: Real-time overview of payment collection status

### 🔧 Technical Features
- **PDF Generation**: Professional receipts using ReportLab
- **CSV Export**: Filtered data export with StreamingResponse
- **Transaction IDs**: Unique identifiers for each payment
- **Payment Methods**: Support for Cash and Online payments
- **Month/Year Tracking**: Organized payment records by period

## API Endpoints

### Payment Management
```
POST /payments/                    - Create new payment
POST /payments/by-name/{name}     - Create payment by student name
PUT /payments/{id}                - Update payment details
DELETE /payments/{id}             - Delete payment
GET /payments/                    - List all payments (with filters)
GET /payments/student/{name}      - Get payments by student name
GET /payments/room/{room_id}      - Get payments by room
```

### Payment Operations
```
POST /payments/{id}/mark-paid     - Mark payment as paid
GET /payments/{id}/receipt        - Download PDF receipt
GET /payments/export/csv          - Export payments to CSV
GET /payments/stats/summary       - Get payment statistics
```

### Query Parameters for Filtering
- `month`: Filter by month (1-12)
- `year`: Filter by year (e.g., 2024)
- `status`: Filter by payment status (Pending/Paid/Failed)

## Database Schema

### Payment Table
```sql
CREATE TABLE payments (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    student_id INTEGER NOT NULL,
    room_id INTEGER NOT NULL,
    date DATETIME NOT NULL,
    amount FLOAT NOT NULL,
    status VARCHAR(20) NOT NULL,
    month INTEGER NOT NULL,
    year INTEGER NOT NULL,
    transaction_id VARCHAR(50) UNIQUE NOT NULL,
    payment_method VARCHAR(20) NOT NULL,
    receipt_generated BOOLEAN NOT NULL DEFAULT FALSE,
    FOREIGN KEY (student_id) REFERENCES students(id),
    FOREIGN KEY (room_id) REFERENCES rooms(id)
);
```

### New Fields Added
- `month`: Payment month (1-12)
- `year`: Payment year
- `transaction_id`: Unique transaction identifier
- `payment_method`: Cash or Online
- `receipt_generated`: Boolean flag for receipt status

## Installation & Setup

### 1. Install Dependencies
```bash
pip install -r requirements.txt
```

### 2. Run Database Migration
```bash
alembic upgrade head
```

### 3. Start the Application
```bash
python app.py
```

## Usage Examples

### Creating a Payment
```javascript
// Frontend JavaScript
const paymentData = {
  student_name: "John Doe",
  amount: 5000,
  month: 12,
  year: 2024,
  payment_method: "Online",
  status: "Pending"
};

await api("/payments/by-name/John Doe", {
  method: "POST",
  body: paymentData
});
```

### Marking Payment as Paid
```javascript
// Student marks payment as paid
await api(`/payments/${paymentId}/mark-paid`, {
  method: "POST",
  body: { payment_method: "Online" }
});
```

### Downloading Receipt
```javascript
// Download PDF receipt
const response = await fetch(`/payments/${paymentId}/receipt`);
const blob = await response.blob();
// Handle blob download...
```

### Exporting CSV
```javascript
// Export filtered payments
const response = await fetch("/payments/export/csv?month=12&year=2024");
const blob = await response.blob();
// Handle blob download...
```

## Frontend Integration

### Admin Dashboard
The admin interface includes:
- Payment statistics cards
- Advanced filtering controls
- Payment management table
- CSV export functionality

### Student Portal
Students can:
- View their payment dues
- Mark payments as completed
- Download payment receipts
- View payment history

### Responsive Design
- Mobile-friendly interface
- Dark/light theme support
- Accessible UI components

## PDF Receipt Features

### Receipt Content
- Hostel name and branding
- Student information (name, ID, room)
- Payment details (amount, method, date)
- Transaction ID and status
- Professional formatting and styling

### Receipt Generation
- Uses ReportLab library
- Professional table layout
- Color-coded sections
- Automatic filename generation

## CSV Export Features

### Exportable Fields
- Student ID and Name
- Room Number
- Month and Year
- Amount and Status
- Transaction ID
- Payment Date and Method

### Filtering Support
- Export all payments
- Filter by month/year
- Filter by payment status
- Custom filename generation

## Security Features

### Payment Validation
- Student existence verification
- Room assignment validation
- Amount validation
- Duplicate transaction prevention

### Access Control
- Role-based interface display
- Admin-only operations
- Student-specific data access

## Error Handling

### Common Error Scenarios
- Student not found
- Invalid payment data
- Database constraints
- File generation failures

### User Feedback
- Clear error messages
- Validation feedback
- Success confirmations
- Loading states

## Testing

### Manual Testing Steps
1. **Create Payment**: Add new payment for existing student
2. **Mark as Paid**: Complete payment process
3. **Generate Receipt**: Download PDF receipt
4. **Export CSV**: Export payment data
5. **Filter Data**: Test month/year/status filters

### API Testing
Use FastAPI's built-in Swagger UI at `/docs` to test all endpoints.

## Troubleshooting

### Common Issues
1. **PDF Generation Fails**: Check ReportLab installation
2. **CSV Export Empty**: Verify database has payment data
3. **Migration Errors**: Ensure database is accessible
4. **Frontend Not Loading**: Check JavaScript console for errors

### Debug Mode
Enable debug logging in the application for detailed error information.

## Future Enhancements

### Planned Features
- Email receipt delivery
- Payment gateway integration
- Advanced reporting
- Bulk payment operations
- Payment reminders
- Financial analytics

### Technical Improvements
- Caching for statistics
- Background task processing
- Enhanced PDF templates
- Data validation improvements

## Support

For technical support or feature requests, please refer to the main project documentation or create an issue in the project repository.

## License

This module is part of the Hostel Management System and follows the same open-source license terms.
