<!-- src/contact.php -->
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <title>Contact</title>
    <link rel="stylesheet" href="../styles.css">
    <style>
        .nav-item { font-weight: bold; }
    </style>
</head>
<body>
    <div class="container">
        <?php
        $message = "Contact Us";
        echo "<h1 class='header'>$message</h1>";
        ?>
        <nav>
            <ul>
                <li class="nav-item">Email</li>
                <li class="nav-item">Phone</li>
            </ul>
        </nav>
    </div>
</body>
</html>