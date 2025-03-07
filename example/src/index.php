<!-- src/index.php -->
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <title>Home Page</title>
    <link rel="stylesheet" href="../styles.css">
</head>
<body>
    <div class="container">
        <header class="header">
            <h1>Welcome</h1>
        </header>
        <?php
        echo '<button class="btn-primary">Click Me</button>';
        ?>
        <nav>
            <ul>
                <li class="nav-item">Home</li>
                <li class="nav-item">About</li>
            </ul>
        </nav>
    </div>
    <script src="scripts.js"></script>
</body>
</html>