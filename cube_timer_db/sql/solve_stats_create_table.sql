CREATE TABLE `solve_times` (
  `id` int(10) NOT NULL AUTO_INCREMENT PRIMARY KEY,
  `the_date` varchar(12),
  `algorithm` varchar(60),
  `solve_time` varchar(10),
  `solve_status` varchar(5),
  `session_average` varchar(10)
);
