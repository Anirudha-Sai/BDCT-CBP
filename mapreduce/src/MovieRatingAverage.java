import java.io.IOException;
import java.util.Locale;

import org.apache.hadoop.conf.Configuration;
import org.apache.hadoop.fs.Path;
import org.apache.hadoop.io.IntWritable;
import org.apache.hadoop.io.Text;
import org.apache.hadoop.mapreduce.Job;
import org.apache.hadoop.mapreduce.Mapper;
import org.apache.hadoop.mapreduce.Reducer;
import org.apache.hadoop.mapreduce.lib.input.FileInputFormat;
import org.apache.hadoop.mapreduce.lib.output.FileOutputFormat;

public class MovieRatingAverage {

    // MAPPER
    public static class RatingMapper
            extends Mapper<Object, Text, Text, IntWritable> {

        private final Text movieId = new Text();
        private final IntWritable rating = new IntWritable();

        @Override
        public void map(Object key, Text value, Context context)
                throws IOException, InterruptedException {

            String[] fields = value.toString().split("\t");

            if (fields.length != 4) {
                return;
            }

            try {
                movieId.set(fields[1]);
                rating.set(Integer.parseInt(fields[2]));

                context.write(movieId, rating);

            } catch (NumberFormatException e) {
                // Ignore malformed records
            }
        }
    }

    // REDUCER
    public static class RatingReducer
            extends Reducer<Text, IntWritable, Text, Text> {

        @Override
        public void reduce(Text key, Iterable<IntWritable> values,
                           Context context)
                throws IOException, InterruptedException {

            long sum = 0;
            long count = 0;

            for (IntWritable value : values) {
                sum += value.get();
                count++;
            }

            if (count > 0) {
                double average = (double) sum / count;

                String result = count + "\t"
                        + String.format(Locale.US, "%.2f", average);

                context.write(key, new Text(result));
            }
        }
    }

    // DRIVER
    public static void main(String[] args) throws Exception {

        if (args.length != 2) {
            System.err.println(
                "Usage: MovieRatingAverage <input path> <output path>"
            );
            System.exit(2);
        }

        Configuration conf = new Configuration();

        Job job = Job.getInstance(conf, "Movie Rating Average");

        job.setJarByClass(MovieRatingAverage.class);

        job.setMapperClass(RatingMapper.class);
        job.setReducerClass(RatingReducer.class);

        job.setMapOutputKeyClass(Text.class);
        job.setMapOutputValueClass(IntWritable.class);

        job.setOutputKeyClass(Text.class);
        job.setOutputValueClass(Text.class);

        FileInputFormat.addInputPath(job, new Path(args[0]));
        FileOutputFormat.setOutputPath(job, new Path(args[1]));

        System.exit(job.waitForCompletion(true) ? 0 : 1);
    }
}
