package com.dawai.repository;

import com.dawai.document.RunDocument;
import org.springframework.data.domain.Page;
import org.springframework.data.domain.Pageable;
import org.springframework.data.mongodb.repository.MongoRepository;

import java.util.Optional;

public interface RunRepository extends MongoRepository<RunDocument, String> {

    Optional<RunDocument> findByRunIdAndUserId(String runId, String userId);

    Page<RunDocument> findByUserIdOrderByCreatedAtDesc(String userId, Pageable pageable);

    long countByUserId(String userId);

    void deleteByRunIdAndUserId(String runId, String userId);
}
