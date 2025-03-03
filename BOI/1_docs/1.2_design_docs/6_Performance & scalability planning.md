# Performance & scalability planning
## Summary of Key Points

1. **Load Testing**  
   - Emphasizes the importance of proactively testing the system’s capacity to handle varying traffic loads.  
   - Helps validate that autoscaling policies work as intended for both serverless (AWS Lambda) and container-based (AWS Fargate) microservices.

2. **Caching Strategy**  
   - Recommends using Amazon ElastiCache (Redis or Memcached) to reduce latency and offload frequent reads or repetitive compliance checks from the primary database.  
   - Particularly useful for:
     - Frequently accessed reference data (e.g., standard compliance rules, lookups).  
     - Reducing repeated computation in microservices.

3. **Global Distribution**  
   - Suggests Amazon CloudFront for caching and efficiently serving static content (front-end files, documents that need low-latency global access, etc.).  
   - Improves application performance for geographically dispersed users by leveraging CloudFront edge locations.

---

## How This Fits Into the Overall Architecture

1. **Microservices (Lambda + Fargate) Autoscaling**  
   - *Load Testing:*  
     - In addition to auto-scaling policies (e.g., CPU/memory for Fargate tasks, concurrency limits for Lambda), regular load testing ensures the infrastructure meets both average and peak demands.  
     - Tools like **AWS Performance Testing** frameworks (e.g., Artillery, Locust, or JMeter) can simulate realistic user load.

   - *Implementation Tip:*  
     - Conduct load tests that account for various scenarios: spikes near compliance deadlines, concurrent file uploads, or back-end batch processes submitting to FinCEN.

2. **Caching Strategy with ElastiCache**  
   - *Use Cases:*  
     - **Caching Repetitive Queries:** For example, quick lookups of compliance rules or repeated identity checks.  
     - **Session Data or Rate Limits:** Could also leverage Redis for tracking session tokens, rate limits, or ephemeral data.  
   - *Implementation Tip:*  
     - Identify read-heavy microservices whose performance can be enhanced by caching.  
     - Carefully define cache invalidation strategies to ensure consistency for sensitive compliance data.

3. **CloudFront for Global Distribution**  
   - *Front-End Optimization:*  
     - Hosting front-end assets on S3 behind CloudFront reduces latency, ensures faster load times, and can drastically improve the mobile/web user experience worldwide.  
   - *Edge Caching:*  
     - Any static files (JS bundles, images, documents that can be publicly cached) will benefit from global edge caching.  
   - *Implementation Tip:*  
     - Implement a versioning strategy or set long cache durations for assets that rarely change.  
     - Consider restricting certain content behind signed URLs if documents are regulated.

---

## Practical Recommendations

1. **Integrate Load Testing Into CI/CD**  
   - Automate baseline load tests in a staging environment after each major deployment.

2. **Monitor and Right-Size Caches**  
   - Use Amazon CloudWatch to track ElastiCache metrics (memory usage, evictions, CPU usage) and set up alerts. Adjust node size or cluster configuration based on observed patterns.

3. **Optimize CloudFront Distributions**  
   - Configure CloudFront behaviors with appropriate cache-control headers, geolocation routing if needed, and custom error pages.  
   - Use AWS WAF with CloudFront if additional edge-level threat protection is required.

4. **Combine Caching Layers**  
   - A layered approach can include CloudFront for global edge caching of static assets and ElastiCache for dynamic data caching closer to microservices.  
   - Always ensure sensitive or frequently updated compliance data remains accurate by defining robust cache invalidation and refresh policies.

