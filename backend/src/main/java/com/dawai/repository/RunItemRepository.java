package com.dawai.repository;

import com.dawai.document.RunItemDocument;
import org.springframework.data.mongodb.repository.MongoRepository;

import java.util.List;

public interface RunItemRepository extends MongoRepository<RunItemDocument, String> {

    List<RunItemDocument> findByRunIdAndUserId(String runId, String userId);

    void deleteByRunIdAndUserId(String runId, String userId);
}
