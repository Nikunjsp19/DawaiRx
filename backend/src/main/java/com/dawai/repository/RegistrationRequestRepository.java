package com.dawai.repository;

import com.dawai.document.RegistrationRequestDocument;
import org.springframework.data.domain.Page;
import org.springframework.data.domain.Pageable;
import org.springframework.data.mongodb.repository.MongoRepository;

import java.util.List;
import java.util.Optional;

public interface RegistrationRequestRepository extends MongoRepository<RegistrationRequestDocument, String> {

    Optional<RegistrationRequestDocument> findByEmailIgnoreCase(String email);

    List<RegistrationRequestDocument> findAllByOrderByRequestedAtDesc();

    Page<RegistrationRequestDocument> findAllByOrderByRequestedAtDesc(Pageable pageable);

    Page<RegistrationRequestDocument> findByStatusOrderByRequestedAtDesc(String status, Pageable pageable);

    long countByStatus(String status);

    boolean existsByEmailIgnoreCaseAndStatus(String email, String status);
}
