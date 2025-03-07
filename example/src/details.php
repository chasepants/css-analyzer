<!-- src/details.php -->
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <title>Details</title>
    <link rel="stylesheet" href="../styles.css">
</head>
<body>
    <div id="main-content">
        <p class="error">Something went wrong</p>
        <?php
        echo '<button data-type="button" class="btn-secondary">Retry</button>';
        ?>
        <input type="text" placeholder="Enter text">
    </div>
</body>
</html>