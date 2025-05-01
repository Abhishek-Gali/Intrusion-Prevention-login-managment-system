<?php
// Database configuration
$host = 'localhost';
$port = 3306;
$username = 'root';
$password = 'root';
$database = 'intrusion_prevention_system';

// Create database connection
try {
    $conn = new mysqli($host, $username, $password, $database, $port);

    // Check connection
    if ($conn->connect_error) {
        throw new Exception("Connection failed: " . $conn->connect_error);
    }

    // Set charset to UTF-8
    $conn->set_charset("utf8mb4");

} catch (Exception $e) {
    // Log error (you can modify this to write to a file or other logging mechanism)
    error_log("Database connection error: " . $e->getMessage());

    // Return error response (modify as needed for your application)
    http_response_code(500);
    echo json_encode(['error' => 'Database connection failed']);
    exit;
}

// Function to close connection (optional, call when done)
function closeConnection($conn) {
    $conn->close();
}
?>