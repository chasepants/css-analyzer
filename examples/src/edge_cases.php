<!-- src/edge_cases.php -->
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <title>Edge Cases</title>
    <link rel="stylesheet" href="../styles.css">
</head>
<body>
    <?php
    // Variable class
    $class = "btn-primary";
    echo "<button class='$class'>Variable Button</button>";

    // Concatenation
    echo '<div class="container ' . 'header">Mixed</div>';

    // Short tag
    ?><div class="nav-item"><?= "Short Tag" ?></div><?php

    // Include
    include 'include.php';
    ?>
</body>
</html>