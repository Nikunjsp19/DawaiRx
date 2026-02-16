package com.dawai.repository;

import com.dawai.document.RunIssueDocument;
import org.springframework.data.mongodb.repository.MongoRepository;

import java.util.List;

public interface RunIssueRepository extends MongoRepository<RunIssueDocument, String> {

    List<RunIssueDocument> findByRunIdAndUserId(String runId, String userId);

    void deleteByRunIdAndUserId(String runId, String userId);
}
