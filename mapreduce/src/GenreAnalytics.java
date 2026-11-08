import java.io.IOException;
import java.util.ArrayList;
import java.util.HashSet;
import java.util.List;
import java.util.Locale;
import java.util.Set;

import org.apache.hadoop.conf.Configuration;
import org.apache.hadoop.fs.Path;
import org.apache.hadoop.io.LongWritable;
import org.apache.hadoop.io.Text;
import org.apache.hadoop.mapreduce.Job;
import org.apache.hadoop.mapreduce.Mapper;
import org.apache.hadoop.mapreduce.Reducer;
import org.apache.hadoop.mapreduce.lib.input.FileInputFormat;
import org.apache.hadoop.mapreduce.lib.input.MultipleInputs;
import org.apache.hadoop.mapreduce.lib.input.TextInputFormat;
import org.apache.hadoop.mapreduce.lib.output.FileOutputFormat;

public class GenreAnalytics {

    // JOB 1: RATING MAPPER
    public static class RatingMapper
            extends Mapper<LongWritable, Text, Text, Text> {

        @Override
        public void map(LongWritable key, Text value, Context context)
                throws IOException, InterruptedException {

            String[] fields = value.toString().split("\t");

            if (fields.length != 4) {
                return;
            }

            String movieId = fields[1];
            String rating = fields[2];

            context.write(
                new Text(movieId),
                new Text("R:" + rating)
            );
        }
    }

    // JOB 1: MOVIE MAPPER
    public static class MovieMapper
            extends Mapper<LongWritable, Text, Text, Text> {

        @Override
        public void map(LongWritable key, Text value, Context context)
                throws IOException, InterruptedException {

            String[] fields = value.toString().split("\t", 3);

            if (fields.length != 3) {
                return;
            }

            String movieId = fields[0];
            String genres = fields[2];

            context.write(
                new Text(movieId),
                new Text("M:" + genres)
            );
        }
    }

    // JOB 1: REDUCE-SIDE JOIN
    public static class JoinReducer
            extends Reducer<Text, Text, Text, Text> {

        @Override
        public void reduce(Text movieId, Iterable<Text> values,
                           Context context)
                throws IOException, InterruptedException {

            List<String> genres = new ArrayList<>();
            List<Integer> ratings = new ArrayList<>();

            for (Text value : values) {

                String record = value.toString();

                if (record.startsWith("M:")) {

                    String genreString = record.substring(2);

                    if (!genreString.equals("Unknown")
                            && !genreString.isEmpty()) {

                        for (String genre : genreString.split(",")) {
                            genres.add(genre);
                        }
                    }

                } else if (record.startsWith("R:")) {

                    try {
                        ratings.add(
                            Integer.parseInt(record.substring(2))
                        );
                    } catch (NumberFormatException e) {
                        // Ignore invalid rating
                    }
                }
            }

            // Exclude movies without assigned genres
            if (genres.isEmpty()) {
                return;
            }

            // Emit movie marker once per genre
            for (String genre : genres) {

                context.write(
                    new Text(genre),
                    new Text("M:" + movieId.toString())
                );

                // Emit every rating for this movie
                for (Integer rating : ratings) {

                    context.write(
                        new Text(genre),
                        new Text("R:" + rating)
                    );
                }
            }
        }
    }

    // JOB 2: GENRE AGGREGATION MAPPER
    public static class GenreMapper
            extends Mapper<LongWritable, Text, Text, Text> {

        @Override
        public void map(LongWritable key, Text value, Context context)
                throws IOException, InterruptedException {

            String[] fields = value.toString().split("\t", 2);

            if (fields.length != 2) {
                return;
            }

            context.write(
                new Text(fields[0]),
                new Text(fields[1])
            );
        }
    }

    // JOB 2: GENRE AGGREGATION REDUCER
    public static class GenreReducer
            extends Reducer<Text, Text, Text, Text> {

        @Override
        public void reduce(Text genre, Iterable<Text> values,
                           Context context)
                throws IOException, InterruptedException {

            long ratingSum = 0;
            long ratingCount = 0;

            Set<String> movieIds = new HashSet<>();

            for (Text value : values) {

                String record = value.toString();

                if (record.startsWith("M:")) {

                    movieIds.add(record.substring(2));

                } else if (record.startsWith("R:")) {

                    try {
                        int rating = Integer.parseInt(
                            record.substring(2)
                        );

                        ratingSum += rating;
                        ratingCount++;

                    } catch (NumberFormatException e) {
                        // Ignore invalid rating
                    }
                }
            }

            double average = ratingCount > 0
                    ? (double) ratingSum / ratingCount
                    : 0.0;

            String result =
                    movieIds.size() + "\t"
                    + ratingCount + "\t"
                    + String.format(Locale.US, "%.2f", average);

            context.write(genre, new Text(result));
        }
    }

    // DRIVER
    public static void main(String[] args) throws Exception {

        if (args.length != 3) {
            System.err.println(
                "Usage: GenreAnalytics <ratings> <movies> <output>"
            );
            System.exit(2);
        }

        Configuration conf = new Configuration();

        Path ratingsPath = new Path(args[0]);
        Path moviesPath = new Path(args[1]);
        Path outputPath = new Path(args[2]);

        Path intermediatePath =
                new Path(args[2] + "_join_tmp");

        // JOB 1: REDUCE-SIDE JOIN
        Job joinJob = Job.getInstance(
            conf, "Movie Ratings and Genres Join"
        );

        joinJob.setJarByClass(GenreAnalytics.class);

        MultipleInputs.addInputPath(
            joinJob,
            ratingsPath,
            TextInputFormat.class,
            RatingMapper.class
        );

        MultipleInputs.addInputPath(
            joinJob,
            moviesPath,
            TextInputFormat.class,
            MovieMapper.class
        );

        joinJob.setReducerClass(JoinReducer.class);

        joinJob.setMapOutputKeyClass(Text.class);
        joinJob.setMapOutputValueClass(Text.class);

        joinJob.setOutputKeyClass(Text.class);
        joinJob.setOutputValueClass(Text.class);

        FileOutputFormat.setOutputPath(
            joinJob, intermediatePath
        );

        if (!joinJob.waitForCompletion(true)) {
            System.exit(1);
        }

        // JOB 2: GENRE AGGREGATION
        Job aggregateJob = Job.getInstance(
            conf, "Genre Wise Analytics"
        );

        aggregateJob.setJarByClass(GenreAnalytics.class);

        aggregateJob.setMapperClass(GenreMapper.class);
        aggregateJob.setReducerClass(GenreReducer.class);

        aggregateJob.setMapOutputKeyClass(Text.class);
        aggregateJob.setMapOutputValueClass(Text.class);

        aggregateJob.setOutputKeyClass(Text.class);
        aggregateJob.setOutputValueClass(Text.class);

        FileInputFormat.addInputPath(
            aggregateJob, intermediatePath
        );

        FileOutputFormat.setOutputPath(
            aggregateJob, outputPath
        );

        System.exit(
            aggregateJob.waitForCompletion(true) ? 0 : 1
        );
    }
}
